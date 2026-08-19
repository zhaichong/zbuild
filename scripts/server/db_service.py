# -*- coding: utf-8 -*-
"""Database service for testing connections and executing safe INSERT statements."""

import datetime
import os
import re
from typing import Any, Dict, List, Optional

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

DB_ALLOWED_DATABASES = {"YHDB"}
DB_MAX_STATEMENTS = 500
DB_MAX_SQL_LENGTH = 64 * 1024
DB_INSERT_RE = re.compile(r"^\s*INSERT\s+(IGNORE\s+)?INTO\s+", re.IGNORECASE)
DB_FORBIDDEN_RE = re.compile(
    r"\b(DROP|ALTER|TRUNCATE|DELETE|UPDATE|GRANT|REVOKE|CREATE|REPLACE|CALL|EXEC|EXECUTE|LOAD\s+DATA|INTO\s+OUTFILE|INTO\s+DUMPFILE|INFORMATION_SCHEMA|SLEEP\s*\(|BENCHMARK\s*\()(?!\w)",
    re.IGNORECASE,
)


def is_private_or_local_host(hostname: str) -> bool:
    """Check if the given hostname/IP is a private LAN or localhost address."""
    h = str(hostname or "").strip().lower().strip("[]")
    if h in ("localhost", "::1", "0.0.0.0"):
        return True

    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", h)
    if m:
        a = [int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))]
        if any(n > 255 for n in a):
            return True
        if a[0] == 10:
            return True
        if a[0] == 127:
            return True
        if a[0] == 0:
            return True
        if a[0] == 169 and a[1] == 254:
            return True
        if a[0] == 192 and a[1] == 168:
            return True
        if a[0] == 172 and 16 <= a[1] <= 31:
            return True
        if a[0] == 100 and 64 <= a[1] <= 127:
            return True
        return False

    if h.startswith("fc") or h.startswith("fd") or h.startswith("fe80"):
        return True
    return False


def assert_db_host_allowed(host: str, env: Optional[Dict[str, str]] = None) -> str:
    """Verify that the database host is allowed (private/local or explicitly in allowlist)."""
    if env is None:
        env = os.environ
    h = str(host or "").strip().lower()
    if not h:
        raise ValueError("数据库主机不能为空")
    if h in ("169.254.169.254", "metadata.google.internal"):
        raise ValueError("禁止访问云元数据地址")

    if not is_private_or_local_host(h):
        allow_str = env.get("ZBUILD_DB_HOST_ALLOWLIST", "")
        allow = [s.strip().lower() for s in allow_str.split(",") if s.strip()]
        if h not in allow:
            raise ValueError(
                f"数据库主机仅允许内网/本机地址，当前: {h}（如需公网主机请设置环境变量 ZBUILD_DB_HOST_ALLOWLIST）"
            )
    return h


def assert_safe_insert_sql(sql: str) -> Optional[str]:
    """Validate that the SQL statement is a safe single INSERT/INSERT IGNORE query."""
    text = str(sql or "").strip()
    if not text or text.startswith("--"):
        return None

    if len(text.encode("utf-8")) > DB_MAX_SQL_LENGTH:
        raise ValueError(f"单条 SQL 过长（>{DB_MAX_SQL_LENGTH} 字节）")

    stripped = re.sub(r";+\s*$", "", text)
    if ";" in stripped:
        raise ValueError("禁止在一条语句中包含多个 SQL（多语句注入）")

    if not DB_INSERT_RE.match(stripped):
        raise ValueError("仅允许 INSERT / INSERT IGNORE 语句")

    # Strip string literals to avoid false positives on user data
    sql_without_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "", stripped)
    sql_without_strings = re.sub(r'"(?:[^"\\]|\\.)*"', "", sql_without_strings)

    if DB_FORBIDDEN_RE.search(sql_without_strings):
        raise ValueError("SQL 包含不允许的关键字")

    return stripped


def test_db_connection(payload: Dict[str, Any], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Test MySQL connection credentials and connectivity."""
    if not HAS_PYMYSQL:
        return {"success": False, "error": "服务端缺少 pymysql 依赖，无法连接 MySQL"}

    try:
        raw_host = (payload or {}).get("host") or "127.0.0.1"
        host = assert_db_host_allowed(raw_host, env=env)
    except Exception as e:
        return {"success": False, "error": str(e)}

    try:
        port = int((payload or {}).get("port") or 3306)
        if not (1 <= port <= 65535):
            return {"success": False, "error": "无效的数据库端口"}
    except (TypeError, ValueError):
        return {"success": False, "error": "无效的数据库端口"}

    user = str((payload or {}).get("user") or "root")[:64]
    password = str((payload or {}).get("password") or "")
    database = str((payload or {}).get("database") or "YHDB")

    if database not in DB_ALLOWED_DATABASES:
        return {"success": False, "error": f"不允许的数据库名: {database}"}

    connection = None
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
            charset="utf8mb4",
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {
            "success": True,
            "message": f"数据库连接成功：{user}@{host}:{port}/{database}",
        }
    except pymysql.MySQLError as err:
        code = err.args[0] if err.args and isinstance(err.args[0], int) else None
        err_msg = str(err)
        if code in (1045, 1044):
            return {"success": False, "error": "数据库认证失败：用户名或密码错误，或账号没有数据库权限"}
        if code == 1049:
            return {"success": False, "error": f"数据库不存在：{database}"}
        if code in (2003, 2002, 2005):
            return {"success": False, "error": f"无法连接数据库服务器 {host}:{port}（{err_msg}）"}
        return {"success": False, "error": f"数据库连接失败（{code or err_msg}）"}
    except Exception as e:
        return {"success": False, "error": f"数据库连接异常: {e}"}
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass


def execute_db_sql(payload: Dict[str, Any], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Safely execute batch INSERT statements against the target MySQL database."""
    if not HAS_PYMYSQL:
        return {
            "success": False,
            "error": "服务端缺少 pymysql 依赖，无法连接 MySQL",
            "logs": "❌ 服务端缺少 pymysql 依赖",
        }

    try:
        raw_host = (payload or {}).get("host") or "127.0.0.1"
        host = assert_db_host_allowed(raw_host, env=env)
    except Exception as e:
        return {"success": False, "error": str(e), "logs": f"❌ {e}"}

    try:
        port = int((payload or {}).get("port") or 3306)
        if not (1 <= port <= 65535):
            return {"success": False, "error": "无效的数据库端口", "logs": "❌ 无效的数据库端口"}
    except (TypeError, ValueError):
        return {"success": False, "error": "无效的数据库端口", "logs": "❌ 无效的数据库端口"}

    user = str((payload or {}).get("user") or "root")[:64]
    password = str((payload or {}).get("password") or "")
    database = str((payload or {}).get("database") or "YHDB")

    if database not in DB_ALLOWED_DATABASES:
        allowed_list = ", ".join(DB_ALLOWED_DATABASES)
        return {
            "success": False,
            "error": f"不允许的数据库名: {database}（仅支持: {allowed_list}）",
            "logs": f"❌ 不允许的数据库名: {database}",
        }

    sql_statements = (payload or {}).get("sqlStatements")
    if not isinstance(sql_statements, list):
        return {"success": False, "error": "sqlStatements 必须是数组", "logs": "❌ sqlStatements 必须是数组"}

    if len(sql_statements) > DB_MAX_STATEMENTS:
        return {
            "success": False,
            "error": f"语句数量超过上限 ({DB_MAX_STATEMENTS})",
            "logs": f"❌ 语句数量超过上限 ({DB_MAX_STATEMENTS})",
        }

    logs: List[str] = []
    success_count = 0
    skipped_count = 0
    error_count = 0

    connection = None
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5,
            autocommit=True,
            charset="utf8mb4",
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{now_str}] 已连接数据库 {user}@{host}:{port}/{database}")

        for i, raw_sql in enumerate(sql_statements):
            idx = i + 1
            total = len(sql_statements)
            try:
                sql = assert_safe_insert_sql(raw_sql)
            except Exception as err:
                error_count += 1
                logs.append(f"❌ [{idx}/{total}] 拒绝执行: {err}")
                continue

            if not sql:
                continue

            try:
                with connection.cursor() as cursor:
                    affected = cursor.execute(sql)
                    if affected > 0:
                        success_count += 1
                        logs.append(f"✅ [{idx}/{total}] 成功写入 {affected} 行")
                    else:
                        skipped_count += 1
                        logs.append(f"⚠️ [{idx}/{total}] 已存在(重复)被自动跳过")
            except Exception as err:
                error_count += 1
                logs.append(f"❌ [{idx}/{total}] 跳过异常行: {err}")

        logs.append("\n===================================")
        logs.append("🎉 数据插入完成统计：")
        logs.append(f"- 成功写入库中: {success_count} 条")
        logs.append(f"- 撞重忽略跳过: {skipped_count} 条")
        logs.append(f"- 异常报错跳过: {error_count} 条")
        logs.append("===================================")

        return {
            "success": True,
            "successCount": success_count,
            "skippedCount": skipped_count,
            "errorCount": error_count,
            "logs": "\n".join(logs),
        }
    except Exception as err:
        err_msg = str(err)
        return {
            "success": False,
            "error": f"无法建立 MySQL 数据库连接 ({err_msg})",
            "logs": f"❌ 无法连接数据库 {user}@{host}:{port}/{database}\n原因: {err_msg}",
        }
    finally:
        if connection:
            try:
                connection.close()
            except Exception:
                pass

# -*- coding: utf-8 -*-
"""Order deployment workflow and SVN tree listing engine.

Provides:
1. list_svn_order_tree: Recursively lists directories and files under an SVN order path.
2. deploy_order_packages: Downloads selected frontend packages from SVN, uploads them to the
   remote Linux server via SSH/SFTP, and extracts them into their respective target directories.
"""

import logging
import os
import shutil
import tempfile
import time
import urllib.parse
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional

from core.errors import UploadError
from runner.protocol import emit, emit_log
from tools.exec import run_process
from uploaders.server import _mkdir_p_sftp, _run_ssh, _shell_quote, build_extract_command
from uploaders.svn import join_svn_url, svn_args


def _format_bytes(size: Optional[int]) -> str:
    """Format byte size into human readable string."""
    if size is None or size < 0:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def _guess_project_name(file_or_dir_name: str) -> Optional[str]:
    """Guess frontend project name from archive or folder name."""
    lower = file_or_dir_name.lower()
    # Strip extensions
    for ext in (".tar.gz", ".tgz", ".zip", ".tar"):
        if lower.endswith(ext):
            lower = lower[:-len(ext)]
            break

    known_projects = [
        "yarward-ntv-frontend",
        "yarward-web-frontend",
        "zhbf-bedhead-frontend",
        "zhbf-fontend",
        "zhbf-frontend",
        "zhbf-web",
        "zbuild",
    ]
    for proj in known_projects:
        if proj.lower() in lower or lower in proj.lower():
            return proj
    return None


def list_svn_order_tree(
    svn_url: str,
    svn_exe: str = "svn",
    username: str = "",
    password: str = "",
    server_upload_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Recursively list contents of an SVN order directory and build a tree.

    Returns a dict with 'success', 'tree', and 'flatList'.
    """
    exe = svn_exe or "svn"
    auth = svn_args(username, password)
    upload_paths = server_upload_paths or {}

    try:
        clean_url = join_svn_url(svn_url)
    except Exception:
        clean_url = svn_url.rstrip("/")

    # 1. 尝试使用 svn list -R --xml 获取递归完整信息
    try:
        r = run_process([exe, "list", "-R", "--xml", clean_url, *auth], timeout=60)
        entries: List[Dict[str, Any]] = []

        if r.returncode == 0 and r.stdout.strip():
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.stdout)
                for entry_elem in root.findall(".//entry"):
                    name_elem = entry_elem.find("name")
                    kind = entry_elem.get("kind", "file")
                    size_elem = entry_elem.find("size")
                    size = int(size_elem.text) if (size_elem is not None and size_elem.text and size_elem.text.isdigit()) else None

                    if name_elem is not None and name_elem.text:
                        rel_path = name_elem.text.replace("\\", "/").strip("/")
                        item_name = PurePosixPath(rel_path).name
                        guessed_proj = _guess_project_name(item_name)
                        is_frontend = bool(
                            kind == "file" and (
                                rel_path.endswith(".tar.gz") or
                                rel_path.endswith(".tgz") or
                                rel_path.endswith(".zip") or
                                "frontend" in rel_path.lower() or
                                "web" in rel_path.lower()
                            )
                        )
                        matched_path = upload_paths.get(guessed_proj or "", "/home/data/web") if is_frontend else ""

                        entries.append({
                            "id": rel_path,
                            "name": item_name,
                            "relativePath": rel_path,
                            "path": f"{clean_url}/{rel_path}",
                            "kind": kind,
                            "size": size,
                            "sizeFormatted": _format_bytes(size),
                            "isFrontendPackage": is_frontend,
                            "matchedProjectName": guessed_proj or "",
                            "matchedServerPath": matched_path,
                        })
            except Exception as parse_err:
                logging.warning("Failed to parse SVN XML output: %s", parse_err)

        # 2. 如果 --xml 解析失败或为空，回退到普通的 svn list -R
        if not entries:
            r_plain = run_process([exe, "list", "-R", clean_url, *auth], timeout=60)
            if r_plain.returncode == 0 and r_plain.stdout.strip():
                for line in r_plain.stdout.strip().splitlines():
                    raw = line.strip()
                    if not raw:
                        continue
                    is_dir = raw.endswith("/")
                    rel_path = raw.replace("\\", "/").strip("/")
                    item_name = PurePosixPath(rel_path).name
                    guessed_proj = _guess_project_name(item_name)
                    is_frontend = bool(
                        not is_dir and (
                            rel_path.endswith(".tar.gz") or
                            rel_path.endswith(".tgz") or
                            rel_path.endswith(".zip") or
                            "frontend" in rel_path.lower() or
                            "web" in rel_path.lower()
                        )
                    )
                    matched_path = upload_paths.get(guessed_proj or "", "/home/data/web") if is_frontend else ""

                    entries.append({
                        "id": rel_path,
                        "name": item_name,
                        "relativePath": rel_path,
                        "path": f"{clean_url}/{rel_path}",
                        "kind": "dir" if is_dir else "file",
                        "size": None,
                        "sizeFormatted": "",
                        "isFrontendPackage": is_frontend,
                        "matchedProjectName": guessed_proj or "",
                        "matchedServerPath": matched_path,
                    })
            elif r.returncode != 0 and r_plain.returncode != 0:
                err_msg = (r_plain.stderr or r.stderr or "").strip()
                return {
                    "success": False,
                    "error": err_msg or f"SVN list 命令执行失败 (退出码: {r_plain.returncode})",
                    "tree": [],
                    "flatList": [],
                }

        # 3. 将扁平列表转换为层级树（Tree View）
        tree = _build_tree_hierarchy(entries)

        return {
            "success": True,
            "tree": tree,
            "flatList": entries,
            "totalFiles": len([e for e in entries if e["kind"] == "file"]),
            "totalDirs": len([e for e in entries if e["kind"] == "dir"]),
        }
    except Exception as exc:
        logging.error("Failed to list SVN order tree: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "tree": [],
            "flatList": [],
        }


def _build_tree_hierarchy(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a nested tree structure from a flat list of path entries."""
    tree: List[Dict[str, Any]] = []
    path_map: Dict[str, Dict[str, Any]] = {}

    # Sort entries by path depth and name
    sorted_entries = sorted(entries, key=lambda x: (x["relativePath"].count("/"), x["relativePath"]))

    for item in sorted_entries:
        node = dict(item)
        node["children"] = []
        path_map[node["relativePath"]] = node

        parts = node["relativePath"].split("/")
        if len(parts) == 1:
            tree.append(node)
        else:
            parent_path = "/".join(parts[:-1])
            if parent_path in path_map:
                path_map[parent_path]["children"].append(node)
            else:
                tree.append(node)

    return tree


def deploy_order_packages(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the deployment of selected frontend packages to a Linux server."""
    svn_url = payload.get("svnUrl", "").rstrip("/")
    svn_exe = payload.get("svn", "") or payload.get("svn_exe", "") or "svn"
    username = payload.get("svnUsername", "")
    password = payload.get("svnPassword", "")

    server_host = payload.get("serverAddress", "")
    server_user = payload.get("serverUsername", "")
    server_pass = payload.get("serverPassword", "")

    selected_files = payload.get("selectedFiles", [])
    if not selected_files:
        return {"success": False, "error": "请勾选至少一个要部署的前端包文件"}

    if not server_host or not server_user:
        return {"success": False, "error": "缺少服务器配置信息（地址/用户名）"}

    emit_log(f"🚀 开始执行测试订单前端部署", level="info")
    emit_log(f"SVN 目录: {svn_url}", level="info")
    emit_log(f"目标服务器: {server_user}@{server_host}", level="info")
    emit_log(f"待部署包数量: {len(selected_files)} 个", level="info")

    import paramiko

    # 1. 建立 SSH/SFTP 连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sftp = None

    temp_dir = tempfile.mkdtemp(prefix="zbuild_order_deploy_")
    remote_temp_dir = f"/tmp/zbuild_deploy_{int(time.time())}"

    success_count = 0
    fail_count = 0
    results: List[Dict[str, Any]] = []

    try:
        emit_log(f"正在连接远程服务器 {server_host}...", level="info")
        ssh.connect(
            hostname=server_host,
            username=server_user,
            password=server_pass,
            timeout=15,
            allow_agent=False,
            look_for_keys=False,
        )
        sftp = ssh.open_sftp()
        emit_log(f"✓ 远程服务器连接成功", level="success")

        _mkdir_p_sftp(sftp, remote_temp_dir)

        total = len(selected_files)
        for idx, item in enumerate(selected_files, start=1):
            file_name = item.get("name", "")
            rel_path = item.get("relativePath", "")
            target_server_path = item.get("targetServerPath", "") or "/home/data/web"
            matched_proj = item.get("matchedProjectName", "") or file_name

            emit({
                "type": "projectStart",
                "project": file_name,
                "steps": ["下载 SVN 包", "上传到服务器", "解压覆盖部署"],
            })

            emit_log(f"[{idx}/{total}] 开始处理包: {file_name}", level="info", project=file_name)
            emit({"type": "step-start", "step": "下载 SVN 包", "project": file_name})

            # Step 1: SVN Export
            try:
                file_svn_url = join_svn_url(svn_url, rel_path)
            except Exception:
                file_svn_url = f"{svn_url}/{urllib.parse.quote(rel_path.strip('/'), safe='/')}"
            local_file_path = os.path.join(temp_dir, file_name)

            auth = svn_args(username, password)
            export_cmd = [svn_exe, "export", "--force", file_svn_url, local_file_path, *auth]
            emit_log(f"正在从 SVN 下载: {file_svn_url}", level="info", project=file_name)
            
            r_export = run_process(export_cmd, timeout=120)
            if r_export.returncode != 0 or not os.path.exists(local_file_path):
                err_msg = f"SVN 下载失败: {r_export.stderr or '文件不存在'}"
                emit_log(err_msg, level="error", project=file_name)
                emit({"type": "step-end", "step": "下载 SVN 包", "success": False, "message": err_msg, "project": file_name})
                emit({"type": "projectResult", "project": file_name, "success": False, "message": err_msg})
                fail_count += 1
                results.append({"name": file_name, "success": False, "error": err_msg})
                continue

            file_size_mb = os.path.getsize(local_file_path) / (1024 * 1024)
            emit_log(f"✓ 下载完成 ({file_size_mb:.2f} MB)", level="success", project=file_name)
            emit({"type": "step-end", "step": "下载 SVN 包", "success": True, "project": file_name})

            # Step 2: SFTP Upload
            emit({"type": "step-start", "step": "上传到服务器", "project": file_name})
            remote_pkg_path = f"{remote_temp_dir}/{file_name}"
            emit_log(f"正在上传至服务器临时路径: {remote_pkg_path}...", level="info", project=file_name)

            try:
                sftp.put(local_file_path, remote_pkg_path)
                emit_log(f"✓ 上传服务器成功", level="success", project=file_name)
                emit({"type": "step-end", "step": "上传到服务器", "success": True, "project": file_name})
            except Exception as up_exc:
                err_msg = f"SFTP 上传失败: {up_exc}"
                emit_log(err_msg, level="error", project=file_name)
                emit({"type": "step-end", "step": "上传到服务器", "success": False, "message": err_msg, "project": file_name})
                emit({"type": "projectResult", "project": file_name, "success": False, "message": err_msg})
                fail_count += 1
                results.append({"name": file_name, "success": False, "error": err_msg})
                continue

            # Step 3: Remote Extract & Replace
            emit({"type": "step-start", "step": "解压覆盖部署", "project": file_name})
            emit_log(f"正在解压覆盖到部署目录: {target_server_path}...", level="info", project=file_name)

            try:
                _mkdir_p_sftp(sftp, target_server_path)
                
                # Check package format
                if file_name.endswith(".zip"):
                    quoted_tmp = _shell_quote(remote_pkg_path)
                    quoted_target = _shell_quote(target_server_path)
                    extract_cmd = f"mkdir -p {quoted_target} && (unzip -o {quoted_tmp} -d {quoted_target} || 7z x -y {quoted_tmp} -o{quoted_target})"
                else:
                    extract_cmd = build_extract_command(matched_proj, remote_pkg_path, target_server_path)

                _run_ssh(ssh, extract_cmd)
                emit_log(f"✓ 远程解压并部署完成 -> {target_server_path}", level="success", project=file_name)
                emit({"type": "step-end", "step": "解压覆盖部署", "success": True, "project": file_name})
                emit({"type": "projectResult", "project": file_name, "success": True})
                success_count += 1
                results.append({"name": file_name, "success": True, "targetPath": target_server_path})
            except Exception as ext_exc:
                err_msg = f"远程解压执行失败: {ext_exc}"
                emit_log(err_msg, level="error", project=file_name)
                emit({"type": "step-end", "step": "解压覆盖部署", "success": False, "message": err_msg, "project": file_name})
                emit({"type": "projectResult", "project": file_name, "success": False, "message": err_msg})
                fail_count += 1
                results.append({"name": file_name, "success": False, "error": err_msg})

        # Cleanup remote temp dir
        try:
            _run_ssh(ssh, f"rm -rf {_shell_quote(remote_temp_dir)}")
        except Exception:
            pass

        emit({"type": "done", "total": total, "successCount": success_count, "failureCount": fail_count})
        emit_log(f"✨ 部署任务全部完成！成功: {success_count}, 失败: {fail_count}", level="success" if fail_count == 0 else "warning")

        return {
            "success": fail_count == 0,
            "total": total,
            "successCount": success_count,
            "failureCount": fail_count,
            "results": results,
        }

    except Exception as exc:
        err_msg = f"部署任务异常: {exc}"
        emit_log(err_msg, level="error")
        emit({"type": "error", "message": err_msg})
        return {"success": False, "error": str(exc)}
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            ssh.close()
        except Exception:
            pass
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def export_svn_file_for_preview(
    file_url: str,
    svn_exe: str = "svn",
    username: str = "",
    password: str = "",
) -> Dict[str, Any]:
    """Export a single SVN file into a local temporary preview directory."""
    if not file_url:
        return {"success": False, "error": "file_url is required"}

    try:
        unquoted = urllib.parse.unquote(file_url.split("?")[0].rstrip("/"))
        file_name = PurePosixPath(unquoted).name or "downloaded_file"

        preview_dir = Path(tempfile.gettempdir()) / "zbuild_preview"
        preview_dir.mkdir(parents=True, exist_ok=True)
        target_path = preview_dir / file_name

        try:
            export_target_url = join_svn_url(file_url)
        except Exception:
            export_target_url = file_url

        cmd = [svn_exe, "export", export_target_url, str(target_path), "--force"]
        cmd.extend(svn_args(username=username, password=password))

        res = run_process(cmd, timeout=30)
        if res.returncode != 0:
            return {
                "success": False,
                "error": f"SVN 导出失败: {res.stderr or res.stdout or '未知错误'}",
            }

        is_text = False
        content = ""
        text_exts = {
            ".sql", ".txt", ".log", ".md", ".json", ".xml", ".yaml", ".yml",
            ".sh", ".bat", ".cmd", ".conf", ".ini", ".properties", ".env",
            ".js", ".ts", ".html", ".css", ".vue", ".java", ".py", ".c", ".cpp", ".h"
        }
        ext = target_path.suffix.lower()
        if ext in text_exts and target_path.stat().st_size < 5 * 1024 * 1024:
            is_text = True
            for enc in ("utf-8", "gbk", "gb2312", "utf-16", "latin1"):
                try:
                    content = target_path.read_text(encoding=enc)
                    break
                except Exception:
                    continue

        return {
            "success": True,
            "filePath": str(target_path),
            "fileName": file_name,
            "isText": is_text,
            "content": content if is_text else "",
            "size": target_path.stat().st_size,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"导出异常: {exc}",
        }


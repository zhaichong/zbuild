# -*- coding: utf-8 -*-
"""Command: server-test."""

from typing import Any, Dict

from runner.cli import register


@register("server-test")
def cmd_server_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test SSH/SFTP connectivity to the target server."""
    host = payload.get("serverAddress", "")
    port = int(payload.get("port", 22) or 22)
    username = payload.get("serverUsername", "")
    password = payload.get("serverPassword", "")

    # If password is empty or sanitized placeholder "[configured]", resolve from saved config
    if password in (None, "", "[configured]"):
        try:
            from core.config import load_config
            cfg = load_config()
            saved_server = cfg.get("server") or {}
            password = saved_server.get("password", "")
            if not host:
                host = saved_server.get("host", "")
            if not username:
                username = saved_server.get("username", "")
        except Exception:
            pass

    if not host or not username:
        return {"success": False, "error": "Missing 'serverAddress' or 'serverUsername'"}

    try:
        from uploaders.server import test_server_connection

        pwd = test_server_connection(host, username, password, port)
        return {"success": True, "message": f"服务器连接成功，当前目录：{pwd}"}
    except ImportError:
        return {"success": False, "error": "paramiko is not installed"}
    except Exception as exc:
        return {"success": False, "error": f"Connection failed: {exc}"}

# -*- coding: utf-8 -*-
"""Command: server-test."""
from __future__ import annotations

from typing import Any

from runner.cli import register


@register("server-test")
def cmd_server_test(payload: dict[str, Any]) -> dict[str, Any]:
    """Test SSH/SFTP connectivity to the target server."""
    host = payload.get("host", "")
    port = payload.get("port", 22)
    username = payload.get("username", "")
    password = payload.get("password", "")

    if not host or not username:
        return {"success": False, "error": "Missing 'host' or 'username'"}

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=10,
        )
        # Quick check: run 'echo ok'
        stdin, stdout, stderr = client.exec_command("echo ok", timeout=5)
        output = stdout.read().decode().strip()
        client.close()

        if output == "ok":
            return {"success": True, "message": "Connection successful"}
        else:
            return {"success": False, "error": f"Unexpected response: {output}"}
    except ImportError:
        return {"success": False, "error": "paramiko is not installed"}
    except Exception as exc:
        return {"success": False, "error": f"Connection failed: {exc}"}

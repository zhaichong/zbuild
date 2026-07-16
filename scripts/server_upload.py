# -*- coding: utf-8 -*-
"""Server upload operations via SSH/SFTP.

This module contains the original server upload logic, updated to
import from the new ``core.constants`` module.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from core.constants import DEFAULT_SERVER_UPLOAD_PATHS
from core.errors import UploadError

logger = logging.getLogger(__name__)


def _get_paramiko():
    """Import and return paramiko, raising UploadError if unavailable."""
    try:
        import paramiko
        return paramiko
    except ImportError:
        raise UploadError("paramiko 未安装，无法使用服务器上传功能。请运行: pip install paramiko")


def server_upload(
    artifact_path: Path,
    host: str,
    port: int,
    username: str,
    password: str,
    remote_dir: str,
    *,
    timeout: float = 15,
) -> dict[str, Any]:
    """Upload an artifact to a remote server via SSH/SFTP.

    Parameters
    ----------
    artifact_path:
        Local path to the artifact file.
    host:
        SSH hostname or IP address.
    port:
        SSH port (typically 22).
    username:
        SSH username.
    password:
        SSH password.
    remote_dir:
        Remote directory to upload to.
    timeout:
        Connection timeout in seconds.

    Returns
    -------
    dict:
        Result dict with keys: success, remote_path, size, duration.

    Raises
    ------
    UploadError:
        If the upload fails.
    """
    paramiko = _get_paramiko()

    remote_file = f"{remote_dir.rstrip('/')}/{artifact_path.name}"
    file_size = artifact_path.stat().st_size
    start_time = time.time()

    logger.info("Uploading %s to %s:%s", artifact_path.name, host, remote_file)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
        )

        # Ensure remote directory exists
        stdin, stdout, stderr = client.exec_command(
            f"mkdir -p {remote_dir}", timeout=10
        )
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            err = stderr.read().decode(errors="replace")
            raise UploadError(f"Failed to create remote directory: {err}")

        # Upload via SFTP
        sftp = client.open_sftp()
        try:
            sftp.put(str(artifact_path), remote_file)

            # Verify
            remote_stat = sftp.stat(remote_file)
            if remote_stat.st_size != file_size:
                raise UploadError(
                    f"Size mismatch after upload: local={file_size}, remote={remote_stat.st_size}"
                )
        finally:
            sftp.close()

        duration = time.time() - start_time
        speed_kbps = (file_size / 1024) / max(duration, 0.1)
        logger.info(
            "Upload complete: %s (%.1f KB, %.1f KB/s)",
            remote_file, file_size / 1024, speed_kbps,
        )

        return {
            "success": True,
            "remote_path": remote_file,
            "host": host,
            "size": file_size,
            "duration": duration,
        }

    except UploadError:
        raise
    except Exception as exc:
        raise UploadError(f"Server upload failed: {exc}") from exc
    finally:
        try:
            client.close()
        except Exception:
            pass


def test_server_connection(
    host: str,
    port: int,
    username: str,
    password: str,
    *,
    timeout: float = 10,
) -> dict[str, Any]:
    """Test SSH connectivity to a server.

    Returns a dict with 'success' and 'message' keys.
    """
    paramiko = _get_paramiko()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
        )
        stdin, stdout, stderr = client.exec_command("echo ok", timeout=5)
        output = stdout.read().decode().strip()
        client.close()

        if output == "ok":
            return {"success": True, "message": "连接成功"}
        else:
            return {"success": False, "message": f"意外响应: {output}"}
    except Exception as exc:
        return {"success": False, "message": f"连接失败: {exc}"}
    finally:
        try:
            client.close()
        except Exception:
            pass


def resolve_upload_path(
    project_name: str,
    custom_path: str = "",
) -> str:
    """Resolve the remote upload path for a project.

    Uses the custom path if provided, otherwise falls back to
    DEFAULT_SERVER_UPLOAD_PATHS.
    """
    if custom_path:
        return custom_path
    return DEFAULT_SERVER_UPLOAD_PATHS.get(project_name, "/home/data/web")

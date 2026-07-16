# -*- coding: utf-8 -*-
"""Server uploader via SSH/SFTP (Buildkite plugin pattern).

Uses paramiko to connect to the target server and upload the artifact
via SFTP to the configured remote path.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from core.constants import DEFAULT_SERVER_UPLOAD_PATHS
from core.errors import UploadError
from uploaders.base import BaseUploader, UploadResult


class ServerUploader(BaseUploader):
    """Upload artifacts to a remote server via SSH/SFTP.

    Configuration keys used:
    - ``server.host``: SSH hostname
    - ``server.port``: SSH port (default 22)
    - ``server.username``: SSH username
    - ``server.password``: SSH password
    - ``projects[].server_upload_path``: remote directory per project
    """

    max_retries = 3

    def upload(
        self,
        artifact: Path,
        config: dict[str, Any],
        log: logging.Logger,
    ) -> UploadResult:
        server_cfg = config.get("server", {})
        host = server_cfg.get("host", "")
        port = server_cfg.get("port", 22)
        username = server_cfg.get("username", "")
        password = server_cfg.get("password", "")

        if not host or not username:
            return UploadResult(
                success=False,
                message="服务器配置不完整: 缺少 host 或 username",
            )

        # Determine remote upload path
        projects = config.get("projects", [])
        project_name = ""
        remote_path = ""
        for proj in projects:
            if proj.get("name"):
                project_name = proj["name"]
                remote_path = proj.get("server_upload_path", "")
                break

        if not remote_path:
            remote_path = DEFAULT_SERVER_UPLOAD_PATHS.get(project_name, "/home/data/web")

        remote_file = f"{remote_path.rstrip('/')}/{artifact.name}"
        file_size = artifact.stat().st_size
        start_time = time.time()

        log.info("Server upload: %s -> %s:%s", artifact.name, host, remote_file)

        try:
            import paramiko
        except ImportError:
            return UploadResult(
                success=False,
                message="paramiko 未安装，无法使用服务器上传",
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=15,
            )

            # Ensure remote directory exists
            stdin, stdout, stderr = client.exec_command(
                f"mkdir -p {remote_path}", timeout=10
            )
            stdout.channel.recv_exit_status()

            # Upload via SFTP
            sftp = client.open_sftp()
            try:
                sftp.put(str(artifact), remote_file)

                # Verify the file was uploaded
                remote_stat = sftp.stat(remote_file)
                if remote_stat.st_size != file_size:
                    return UploadResult(
                        success=False,
                        target_url=f"{host}:{remote_file}",
                        message=f"文件大小不匹配: 本地 {file_size} vs 远程 {remote_stat.st_size}",
                        duration_seconds=time.time() - start_time,
                    )
            finally:
                sftp.close()

            duration = time.time() - start_time
            log.info("Upload complete: %s (%.1f KB/s)",
                     remote_file,
                     (file_size / 1024) / max(duration, 0.1))

            return UploadResult(
                success=True,
                target_url=f"{host}:{remote_file}",
                message=f"已上传到服务器: {remote_file}",
                bytes_uploaded=file_size,
                duration_seconds=duration,
            )

        except Exception as exc:
            return UploadResult(
                success=False,
                target_url=f"{host}:{remote_file}",
                message=f"SSH/SFTP 上传失败: {exc}",
                duration_seconds=time.time() - start_time,
            )
        finally:
            try:
                client.close()
            except Exception:
                pass

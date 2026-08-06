# -*- coding: utf-8 -*-
"""Server uploader via SSH/SFTP with smart extract-and-replace.

Uploads the artifact to a temporary path on the server, then extracts
it into the target directory. For most projects, the extraction first
deletes matching top-level directories to prevent stale files.
"""

import logging
import posixpath
import tarfile
import time
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Dict

from core.constants import DEFAULT_SERVER_UPLOAD_PATHS
from core.errors import UploadError
from uploaders.base import BaseUploader, UploadResult, as_log_fn


# ── Helpers ──────────────────────────────────────────────────────────

def _run_ssh(ssh, command: str) -> str:
    """Execute a remote command and return stdout. Raises on non-zero exit."""
    _stdin, stdout, stderr = ssh.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    if exit_code != 0:
        raise RuntimeError(error or output or f"服务器命令执行失败：{command}")
    return output


def _mkdir_p_sftp(sftp, remote_dir: str) -> None:
    """Recursively create remote directories via SFTP."""
    is_absolute = remote_dir.startswith("/")
    parts = [p for p in remote_dir.split("/") if p]
    current = ""
    for idx, part in enumerate(parts):
        if idx == 0 and is_absolute:
            current = f"/{part}"
        elif current == "":
            current = part
        else:
            current = f"{current}/{part}"
        try:
            sftp.stat(current)
        except IOError:
            sftp.mkdir(current)


def _shell_quote(value: str) -> str:
    """Safely quote a value for shell commands."""
    return "'" + value.replace("'", "'\\''") + "'"


def _archive_safety_error(artifact: Path) -> str:
    """Return an error when a tar member could escape the target directory."""
    try:
        with tarfile.open(artifact, "r:*") as archive:
            for member in archive.getmembers():
                member_path = PurePosixPath(member.name.replace("\\", "/"))
                if member_path.is_absolute() or ".." in member_path.parts:
                    return f"不安全的归档路径: {member.name}"
                if member.issym() or member.islnk():
                    link_path = PurePosixPath(member.linkname.replace("\\", "/"))
                    if link_path.is_absolute() or ".." in link_path.parts:
                        return f"不安全的归档链接: {member.name} -> {member.linkname}"
    except (tarfile.TarError, OSError) as exc:
        return f"无法读取产物压缩包: {exc}"
    return ""


def build_extract_command(project_name: str, remote_tmp: str, target_dir: str) -> str:
    """Build the shell command to extract an archive on the server.

    For ``yarward-web-frontend``: simple extract (overwrite only).
    For all other projects: smart delete-then-extract — removes matching
    top-level directories before extracting to prevent stale files.
    """
    quoted_tmp = _shell_quote(remote_tmp)
    quoted_target = _shell_quote(target_dir)
    if project_name == "yarward-web-frontend":
        return (
            f"mkdir -p {quoted_target} && "
            f"(tar -xzf {quoted_tmp} -C {quoted_target} 2>/dev/null "
            f"|| tar -xf {quoted_tmp} -C {quoted_target})"
        )
    return (
        f"mkdir -p {quoted_target} && "
        f"entries=$(tar -tzf {quoted_tmp} 2>/dev/null || tar -tf {quoted_tmp}) && "
        "printf '%s\\n' \"$entries\" | awk -F/ 'NF && $1 != \".\" {print $1}' | sort -u | "
        "while IFS= read -r item; do "
        "[ -n \"$item\" ] || continue; "
        f"rm -rf -- {quoted_target}/\"$item\"; "
        "done && "
        f"(tar -xzf {quoted_tmp} -C {quoted_target} 2>/dev/null "
        f"|| tar -xf {quoted_tmp} -C {quoted_target})"
    )


def test_server_connection(host: str, username: str, password: str, port: int = 22) -> str:
    """Test SSH connectivity by running ``pwd`` on the server."""
    try:
        import paramiko
    except ImportError as exc:
        raise RuntimeError("当前 Python 环境缺少 paramiko，无法检测服务器连接。") from exc

    from uploaders.ssh_policy import open_ssh_client

    ssh = open_ssh_client(paramiko)
    try:
        ssh.connect(hostname=host, port=port, username=username, password=password, timeout=15)
        output = _run_ssh(ssh, "pwd")
    finally:
        ssh.close()
    return output.strip() or "OK"


# ── Uploader class ───────────────────────────────────────────────────

class ServerUploader(BaseUploader):
    """Upload artifacts to a remote server via SSH/SFTP with smart extract.

    The upload flow:
    1. Upload artifact to a temporary path (``/tmp/<stem>-<ts><suffix>``)
    2. Extract the archive on the server into the target directory
    3. Clean up the temporary file

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
        config: Dict[str, Any],
        log: Any = None,
        project_name: str = "",
    ) -> UploadResult:
        log_fn = as_log_fn(log)
        server_cfg = config.get("server", {})
        host = server_cfg.get("host", "")
        port = int(server_cfg.get("port", 22) or 22)
        username = server_cfg.get("username", "")
        password = server_cfg.get("password", "")

        if not host or not username:
            return UploadResult(
                success=False,
                message="服务器配置不完整: 缺少 host 或 username",
            )

        safety_error = _archive_safety_error(artifact)
        if safety_error:
            return UploadResult(success=False, message=f"产物压缩包不安全: {safety_error}")

        # Determine remote upload path from the matching project config or global server_upload_paths
        remote_path = ""
        for proj in config.get("projects", []):
            if proj.get("name") == project_name:
                remote_path = proj.get("server_upload_path", "")
                break

        if not remote_path:
            server_paths = config.get("server_upload_paths", {})
            if isinstance(server_paths, dict):
                remote_path = server_paths.get(project_name, "")

        if not remote_path:
            remote_path = DEFAULT_SERVER_UPLOAD_PATHS.get(project_name, "/home/data/web")

        file_size = artifact.stat().st_size
        start_time = time.time()

        # Temporary path on the server
        if artifact.name.endswith(".tar.gz"):
            base_name = artifact.name[:-7]
            ext = ".tar.gz"
        else:
            base_name = artifact.stem
            ext = artifact.suffix

        remote_tmp = posixpath.join(
            "/tmp", f"{base_name}-{int(time.time())}{ext}"
        )
        quoted_tmp = _shell_quote(remote_tmp)

        log_fn(f"准备上传到服务器: {artifact.name} -> {host}:{remote_path}")

        try:
            import paramiko
        except ImportError:
            return UploadResult(
                success=False,
                message="paramiko 未安装，无法使用服务器上传",
            )

        from uploaders.ssh_policy import open_ssh_client

        client = open_ssh_client(paramiko)

        try:
            log_fn(f"正在连接服务器 {host}:{port} ...")
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=20,
            )

            # Step 1: Upload to temp path via SFTP
            sftp = client.open_sftp()
            try:
                _mkdir_p_sftp(sftp, remote_path)
                log_fn(f"正在上传临时包到服务器: {remote_tmp} ({file_size / 1024 / 1024:.2f} MB)")
                sftp.put(str(artifact), remote_tmp)
            finally:
                sftp.close()

            # Step 2: Extract on the server
            log_fn(f"正在服务器上解压产物到: {remote_path}")
            extract_cmd = build_extract_command(project_name, remote_tmp, remote_path)
            _run_ssh(client, extract_cmd)

            # Step 3: Clean up temp file
            log_fn("正在清理服务器临时包...")
            _run_ssh(client, f"rm -f {quoted_tmp}")

            duration = time.time() - start_time
            log_fn(f"服务器上传解压完成 (耗时 {duration:.1f}s)")

            return UploadResult(
                success=True,
                target_url=f"{host}:{remote_path}",
                message=f"已上传并解压到服务器: {remote_path}",
                bytes_uploaded=file_size,
                duration_seconds=duration,
            )

        except Exception as exc:
            return UploadResult(
                success=False,
                target_url=f"{host}:{remote_path}",
                message=f"SSH/SFTP 上传失败: {exc}",
                duration_seconds=time.time() - start_time,
            )
        finally:
            try:
                client.close()
            except Exception:
                pass

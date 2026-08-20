# -*- coding: utf-8 -*-
"""SVN uploader (Buildkite plugin pattern).

Handles the full SVN workflow: ensure the remote directory exists,
check out a working copy, copy the artifact in, and commit.
All SVN commands include authentication credentials.
"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from core.constants import DEFAULT_SVN_ROOT, UPGRADE_DOC_NAME, UPGRADE_DOC_PATH
from core.errors import UploadError
from tools.exec import run_process
from uploaders.base import BaseUploader, UploadResult


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def join_svn_url(root: str, *segments: str) -> str:
    """Join SVN URL with proper encoding, avoiding double slashes."""
    decoded_segments = [unquote(segment).strip() for segment in segments]
    if any(
        part in (".", "..")
        for segment in decoded_segments
        for part in segment.replace(chr(92), "/").split("/")
    ):
        raise ValueError("SVN path segments cannot contain '.' or '..'")
    split = urlsplit(root.rstrip("/"))
    root_parts = [p for p in unquote(split.path).split("/") if p]
    all_parts = root_parts + [s.strip().strip("/") for s in segments if s.strip()]
    encoded_path = "/" + "/".join(quote(unquote(part), safe="") for part in all_parts)
    return urlunsplit((split.scheme, split.netloc, encoded_path, "", ""))


# ---------------------------------------------------------------------------
# SVN auth args
# ---------------------------------------------------------------------------

def svn_args(
    username: str,
    password: str,
    *,
    config_dir: Optional[str] = None,
) -> List[str]:
    """Return common SVN CLI arguments for non-interactive authentication.

    Password handling
    -----------------
    SVN has no portable "password from file" flag. When *config_dir* is set we
    use an isolated config directory (no global auth cache pollution). The
    password is still passed via ``--password`` for the duration of the command
    (visible briefly in the process list on some OSes); logs redact it.

    Certificate trust
    -----------------
    By default, self-signed internal SVN servers are accepted (hospital LAN).
    Set ``ZBUILD_SVN_STRICT=1`` to require valid certificates.
    """
    args = ["--non-interactive"]
    strict = os.environ.get("ZBUILD_SVN_STRICT", "").strip().lower() in {"1", "true", "yes"}
    if not strict:
        args.extend([
            "--trust-server-cert-failures",
            "unknown-ca,cn-mismatch,expired,not-yet-valid,other",
            "--trust-server-cert",
        ])
    if config_dir:
        args.extend(["--config-dir", config_dir])
        # Private config-dir may cache auth for multi-step ops without re-exporting
        # credentials to the user profile. Still pass password when provided.
    else:
        args.append("--no-auth-cache")
    if username and username.strip():
        args.extend(["--username", username.strip()])
    if password and password.strip():
        # Prefer not to leave secrets in argv longer than needed; callers using
        # an isolated config_dir still must pass once to seed the session.
        args.extend(["--password", password.strip()])
    return args


def _svn_exe(config: Dict[str, Any]) -> str:
    """Return the SVN executable path from config or system."""
    return config.get("svn_exe") or "svn"


def _as_log_fn(log):
    """Normalize *log* into a callable accepting a single message string."""
    if log is None or callable(log):
        return log
    info = getattr(log, "info", None)
    if callable(info):
        return lambda msg: info("%s", msg)
    return None


def _get_svn_creds(config: Dict[str, Any]) -> Tuple[str, str]:
    """Extract SVN credentials from config."""
    svn_creds = config.get("svn_credentials", {})
    username = svn_creds.get("username", "")
    password = svn_creds.get("password", "")
    return username, password


# ---------------------------------------------------------------------------
# SVN operations
# ---------------------------------------------------------------------------

def svn_info(svn: str, url: str, username: str, password: str) -> bool:
    """Check if an SVN URL exists (svn info)."""
    exe = svn or "svn"
    r = run_process([exe, "info", url, *svn_args(username, password)], timeout=30)
    return r.returncode == 0


def list_svn_contents(
    svn_url: str,
    svn_exe: str = "svn",
    username: str = "",
    password: str = "",
) -> List[Dict[str, str]]:
    """List the contents of an SVN directory.

    Returns a list of dicts with 'name', 'kind' (file/dir), and 'rev'.
    """
    exe = svn_exe or "svn"
    svn_url = join_svn_url(svn_url)
    auth = svn_args(username, password)
    
    # 1. 尝试使用 --xml 获取结构化目录列表
    try:
        r = run_process([exe, "list", "--xml", svn_url, *auth], timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            entries: List[Dict[str, str]] = []
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.stdout)
                for entry_elem in root.findall(".//entry"):
                    name_elem = entry_elem.find("name")
                    kind = entry_elem.get("kind", "file")
                    rev = entry_elem.get("revision", "")
                    if name_elem is not None and name_elem.text:
                        entries.append({
                            "name": name_elem.text.rstrip("/"),
                            "kind": kind,
                            "rev": rev,
                        })
                if entries:
                    return entries
            except Exception as exc:
                logging.warning("Failed to parse SVN list XML: %s", exc)

        # 如果 --xml 无输出或失败，回退到普通文本 svn list
        r_plain = run_process([exe, "list", svn_url, *auth], timeout=30)
        if r_plain.returncode == 0 and r_plain.stdout.strip():
            entries = []
            for line in r_plain.stdout.strip().splitlines():
                clean_name = line.strip().rstrip("/")
                if clean_name:
                    entries.append({
                        "name": clean_name,
                        "kind": "dir" if line.strip().endswith("/") else "file",
                        "rev": "",
                    })
            return entries

        detail = (r_plain.stderr or r_plain.stdout or r.stderr or r.stdout).strip()
        logging.warning("SVN list returned exit code %d. stderr: %s", r.returncode, detail)
        raise UploadError(detail or f"svn list failed with exit code {r.returncode}")
    except Exception as exc:
        if isinstance(exc, UploadError):
            raise
        logging.error("SVN list execution error: %s", exc)
        raise UploadError(f"SVN list execution error: {exc}") from exc


def ensure_svn_path(
    svn: str,
    root: str,
    segments: List[str],
    username: str,
    password: str,
    log=None,
) -> str:
    """Ensure the SVN directory path exists, creating each segment if needed.

    Iterates through segments one by one, checking existence before creating.
    Returns the final SVN URL.
    """
    log = _as_log_fn(log)
    current: List[str] = []
    for segment in segments:
        current.append(segment)
        url = join_svn_url(root, *current)
        if svn_info(svn, url, username, password):
            if log:
                log(f"SVN目录已存在：{url}")
            continue
        if log:
            log(f"创建SVN目录：{url}")
        result = run_process(
            [svn, "mkdir", url, "-m", f"Create remote folder {url}", *svn_args(username, password)],
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or f"svn mkdir failed: {url}")
    return join_svn_url(root, *segments)


def _is_same_project_artifact(old_name: str, new_name: str, project_name: str = "") -> bool:
    """Check if old_name is an older artifact from the same project as new_name."""
    if old_name == new_name:
        return False
    if not old_name.endswith(".tar.gz"):
        return False

    def _get_prefixes(name: str) -> Tuple[str, str]:
        base = name[:-7] if name.endswith(".tar.gz") else name
        prefix = base.split("_", 1)[0].lower()
        short = prefix
        if short.startswith("yarward-"):
            short = short[len("yarward-"):]
        if short.endswith("-frontend"):
            short = short[:-len("-frontend")]
        return prefix, short

    target_prefixes = set()
    if project_name:
        p_clean = project_name.lower().strip()
        target_prefixes.add(p_clean)
        short_p = p_clean
        if short_p.startswith("yarward-"):
            short_p = short_p[len("yarward-"):]
        if short_p.endswith("-frontend"):
            short_p = short_p[:-len("-frontend")]
        if short_p:
            target_prefixes.add(short_p)

    new_p, new_s = _get_prefixes(new_name)
    if new_p:
        target_prefixes.add(new_p)
    if new_s:
        target_prefixes.add(new_s)

    old_p, old_s = _get_prefixes(old_name)
    return (old_p in target_prefixes) or (bool(old_s) and old_s in target_prefixes)


def upload_artifact(
    artifact_path: Path,
    svn_url: str,
    svn_exe: str = "svn",
    username: str = "",
    password: str = "",
    skip_commit: bool = False,
    commit_message: str = "",
    log=None,
    project_name: str = "",
) -> UploadResult:
    """Upload an artifact to SVN by checking out, copying, and committing.

    Only removes old artifacts with the same project prefix (not all files).
    Also copies the upgrade documentation if available.
    """
    log = _as_log_fn(log)
    start_time = time.time()
    work_dir = None
    # Isolated config-dir: auth material stays out of the user profile; multi-step
    # ops share one dir so we do not write credentials into ~/.subversion.
    cfg_dir = tempfile.mkdtemp(prefix="zbuild-svn-cfg-")

    def _auth(with_password: bool = True) -> List[str]:
        return svn_args(
            username,
            password if with_password else "",
            config_dir=cfg_dir,
        )

    try:
        # Create a temporary working directory
        work_dir = tempfile.mkdtemp(prefix="zbuild-svn-")
        parent_url = svn_url.rsplit("/", 1)[0] if "/" in svn_url else svn_url

        if log:
            log(f"正在检出 SVN 目录: {parent_url} ...")

        # Checkout the parent directory
        r = run_process(
            [svn_exe, "checkout", parent_url, work_dir, *_auth(True)],
            timeout=60,
        )
        if r.returncode != 0:
            # Directory might not exist, try creating it
            try:
                leaf_segment = parent_url.rsplit("/", 1)[-1]
                ensure_svn_path(svn_exe, parent_url.rsplit("/", 1)[0], [leaf_segment], username, password, log)
            except Exception:
                pass
            r = run_process(
                [svn_exe, "checkout", parent_url, work_dir, *_auth(True)],
                timeout=60,
            )
            if r.returncode != 0:
                err_msg = r.stderr or r.stdout
                if log:
                    log(f"SVN 检出失败: {err_msg}")
                return UploadResult(
                    success=False,
                    message=f"SVN checkout failed: {err_msg}",
                )

        if log:
            log("SVN 目录检出成功")

        dest_name = artifact_path.name
        dest_path = Path(work_dir) / dest_name

        # Remove old artifacts with the SAME project prefix
        for old_artifact in list(Path(work_dir).glob("*.tar.gz")):
            if _is_same_project_artifact(old_artifact.name, dest_name, project_name):
                if log:
                    log(f"发现历史产物，准备清理: {old_artifact.name}")
                # Check SVN status before deleting
                status = run_process([svn_exe, "status", str(old_artifact)], cwd=work_dir)
                status_text = status.stdout.strip()
                if status.returncode == 0 and status_text.startswith("?"):
                    # Unversioned file, just delete
                    old_artifact.unlink()
                    continue
                if status.returncode == 0 and status_text.startswith("!"):
                    # Already missing, skip
                    continue
                # Versioned file - use svn delete (with auth)
                remove = run_process(
                    [svn_exe, "delete", str(old_artifact), *_auth(True)],
                    cwd=work_dir,
                )
                if remove.returncode != 0 and "is not under version control" not in (remove.stderr or remove.stdout):
                    raise RuntimeError(remove.stderr or remove.stdout)
                if remove.returncode != 0 and old_artifact.exists():
                    old_artifact.unlink()
                if log:
                    log(f"已清理历史产物: {old_artifact.name}")

        # Copy the artifact into the working copy
        shutil.copy2(str(artifact_path), str(dest_path))
        file_size = dest_path.stat().st_size
        if log:
            log(f"已写入最新构建产物: {dest_name} ({file_size / 1024 / 1024:.2f} MB)")

        # Copy upgrade documentation if available
        if UPGRADE_DOC_PATH.exists():
            upgrade_target = Path(work_dir) / UPGRADE_DOC_NAME
            if upgrade_target.exists():
                if log:
                    log(f"升级说明已存在，跳过上传: {UPGRADE_DOC_NAME}")
            else:
                shutil.copy2(str(UPGRADE_DOC_PATH), str(upgrade_target))
                if log:
                    log(f"补充上传升级说明: {UPGRADE_DOC_NAME}")
        else:
            if log:
                log(f"未找到升级说明文件，跳过补充: {UPGRADE_DOC_PATH}")

        if skip_commit:
            if log:
                log("已配置跳过提交 (skip_svn_commit=True)")
            return UploadResult(
                success=True,
                target_url=svn_url,
                message="文件已复制到工作副本（未提交）",
                bytes_uploaded=file_size,
                duration_seconds=time.time() - start_time,
            )

        # SVN add + commit
        if log:
            log("正在添加文件到 SVN (svn add)...")
        r = run_process(
            [svn_exe, "add", ".", "--force", *_auth(True)],
            cwd=work_dir,
        )
        if r.returncode != 0:
            err_msg = r.stderr or r.stdout
            if log:
                log(f"SVN add 失败: {err_msg}")
            return UploadResult(
                success=False,
                target_url=svn_url,
                message=f"SVN add failed: {err_msg}",
                duration_seconds=time.time() - start_time,
            )

        commit_msg = commit_message or f"上传构建产物: {dest_name}"
        if log:
            log(f"正在提交到 SVN: {commit_msg} ...")

        r = run_process(
            [svn_exe, "commit", ".", "-m", commit_msg, *_auth(True)],
            cwd=work_dir,
            timeout=120,
        )
        if r.returncode != 0:
            err_msg = r.stderr or r.stdout
            if log:
                log(f"SVN commit 失败: {err_msg}")
            return UploadResult(
                success=False,
                target_url=svn_url,
                message=f"SVN commit failed: {err_msg}",
                duration_seconds=time.time() - start_time,
            )

        commit_out = (r.stdout or "").strip()
        if log:
            if commit_out:
                for line in commit_out.splitlines():
                    if line.strip():
                        log(f"SVN: {line.strip()}")
            else:
                log("SVN: 提交完成（工作副本无文件变更）")

        rev_info = ""
        for line in commit_out.splitlines():
            if "revision" in line.lower() or "版本" in line:
                rev_info = f" ({line.strip()})"
                break

        return UploadResult(
            success=True,
            target_url=svn_url,
            message=f"已成功提交到 SVN: {dest_name}{rev_info}",
            bytes_uploaded=file_size,
            duration_seconds=time.time() - start_time,
        )

    except Exception as exc:
        if log:
            log(f"SVN 上传异常: {exc}")
        return UploadResult(
            success=False,
            target_url=svn_url,
            message=f"SVN upload error: {exc}",
            duration_seconds=time.time() - start_time,
        )
    finally:
        # Clean up working directory and isolated SVN config-dir (may hold auth)
        if work_dir and Path(work_dir).exists():
            shutil.rmtree(work_dir, ignore_errors=True)
        if cfg_dir and Path(cfg_dir).exists():
            shutil.rmtree(cfg_dir, ignore_errors=True)


class SvnUploader(BaseUploader):
    """Upload artifacts to SVN.

    The SVN URL is constructed from the config's ``svn_root`` and the
    project's ``svn_leaf`` name.  All SVN commands include authentication.
    """

    max_retries = 2

    def upload(
        self,
        artifact: Path,
        config: Dict[str, Any],
        log: Any = None,
        project_name: str = "",
    ) -> UploadResult:
        log_fn = _as_log_fn(log)
        svn_root = config.get("svn_root", DEFAULT_SVN_ROOT)
        svn_exe = _svn_exe(config)
        skip_commit = config.get("skip_svn_commit", False)
        username, password = _get_svn_creds(config)
        hospital_name = config.get("hospital_name", "")
        order_no = config.get("order_no", "")

        if not username or not password:
            if log_fn:
                log_fn("警告：SVN 凭据未配置，上传可能会失败")

        # All packages for an order normally share one directory ("前端" by
        # default).  A project-specific leaf is retained only for legacy
        # configurations that have not enabled the unified directory setting.
        svn_leaf = ""
        proj_branch = ""
        proj_svn_root = config.get("project_svn_roots", {}).get(project_name)
        for proj in config.get("projects", []):
            if proj.get("name") == project_name:
                svn_leaf = proj.get("svn_leaf", project_name)
                proj_branch = proj.get("branch", "")
                if proj.get("svn_root"):
                    proj_svn_root = proj.get("svn_root")
                break
        svn_root = proj_svn_root or config.get("svn_root", DEFAULT_SVN_ROOT)
        if not svn_leaf and project_name:
            svn_leaf = project_name
        if not svn_leaf:
            svn_leaf = artifact.stem.replace(".tar", "")
        unified_directory = str(config.get("svn_upload_directory") or "").strip()
        if unified_directory:
            svn_leaf = unified_directory

        # Build SVN URL with hospital/order hierarchy:
        # svn_root/hospital_name/order_no/svn_leaf/artifact
        path_segments = []
        if hospital_name:
            path_segments.append(hospital_name)
        if order_no:
            path_segments.append(order_no)
        if svn_leaf:
            path_segments.append(svn_leaf)

        # Ensure the directory path exists
        if path_segments:
            dir_url = join_svn_url(svn_root, *path_segments)
            try:
                ensure_svn_path(svn_exe, svn_root, path_segments, username, password, log_fn)
            except Exception as exc:
                if log_fn:
                    log_fn(f"SVN 目录创建失败: {exc}")
                return UploadResult(
                    success=False,
                    message=f"SVN目录创建失败: {exc}",
                )
        else:
            dir_url = svn_root

        svn_url = join_svn_url(dir_url, artifact.name)
        if log_fn:
            log_fn(f"SVN 上传目标: {svn_url}")

        # Build rich commit message with full context
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = (
            f"Auto upload {project_name} branch {proj_branch} "
            f"hospital {hospital_name} order {order_no} at {timestamp}"
        )

        return upload_artifact(
            artifact, svn_url, svn_exe,
            username=username,
            password=password,
            skip_commit=skip_commit,
            commit_message=commit_msg,
            log=log_fn,
            project_name=project_name,
        )

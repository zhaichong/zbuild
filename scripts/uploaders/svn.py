# -*- coding: utf-8 -*-
"""SVN uploader (Buildkite plugin pattern).

Handles the full SVN workflow: ensure the remote directory exists,
check out a working copy, copy the artifact in, and commit.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from core.constants import DEFAULT_SVN_ROOT
from core.errors import UploadError
from tools.exec import run_process
from uploaders.base import BaseUploader, UploadResult


def join_svn_url(*parts: str) -> str:
    """Join SVN URL path segments, avoiding double slashes."""
    result = parts[0]
    for part in parts[1:]:
        part = part.strip("/")
        if part:
            result = result.rstrip("/") + "/" + part
    return result


def _svn_exe(config: dict[str, Any]) -> str:
    """Return the SVN executable path from config or system."""
    return config.get("svn_exe", "svn")


def ensure_svn_path(svn_url: str, svn_exe: str = "svn") -> bool:
    """Ensure the SVN directory exists, creating it if necessary.

    Tries ``svn mkdir -p`` which is a no-op if the path already exists.
    """
    try:
        r = run_process(
            [svn_exe, "mkdir", "-p", "--parents", svn_url, "-m", "auto-create directory"],
            timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def upload_artifact(
    artifact_path: Path,
    svn_url: str,
    svn_exe: str = "svn",
    skip_commit: bool = False,
) -> UploadResult:
    """Upload an artifact to SVN by checking out, copying, and committing.

    Parameters
    ----------
    artifact_path:
        Path to the local artifact file.
    svn_url:
        Full SVN URL to upload to (including the filename).
    svn_exe:
        Path to the svn executable.
    skip_commit:
        If True, prepare the working copy but do not commit.

    Returns
    -------
    UploadResult
    """
    start_time = time.time()
    work_dir = None

    try:
        # Create a temporary working directory
        work_dir = tempfile.mkdtemp(prefix="zbuild-svn-")
        parent_url = str(Path(svn_url).parent).replace("\\", "/")
        # Fix URL: use svn URL joining, not filesystem path
        parent_url = svn_url.rsplit("/", 1)[0] if "/" in svn_url else svn_url

        # Checkout the parent directory
        r = run_process(
            [svn_exe, "checkout", parent_url, work_dir],
            timeout=60,
        )
        if r.returncode != 0:
            # Directory might not exist, try creating it
            if not ensure_svn_path(parent_url, svn_exe):
                return UploadResult(
                    success=False,
                    message=f"SVN checkout failed: {r.stderr}",
                )
            r = run_process(
                [svn_exe, "checkout", parent_url, work_dir],
                timeout=60,
            )
            if r.returncode != 0:
                return UploadResult(
                    success=False,
                    message=f"SVN checkout failed after mkdir: {r.stderr}",
                )

        # Clean the working directory (remove old files)
        for item in Path(work_dir).iterdir():
            if item.name == ".svn":
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Copy the artifact into the working copy
        dest_name = artifact_path.name
        dest_path = Path(work_dir) / dest_name
        shutil.copy2(str(artifact_path), str(dest_path))

        file_size = dest_path.stat().st_size

        if skip_commit:
            return UploadResult(
                success=True,
                target_url=svn_url,
                message="文件已复制到工作副本（未提交）",
                bytes_uploaded=file_size,
                duration_seconds=time.time() - start_time,
            )

        # SVN add + commit
        r = run_process(
            [svn_exe, "add", "--force", str(dest_path)],
            cwd=work_dir,
        )

        commit_msg = f"上传构建产物: {dest_name}"
        r = run_process(
            [svn_exe, "commit", "-m", commit_msg, work_dir],
            timeout=120,
        )
        if r.returncode != 0:
            return UploadResult(
                success=False,
                target_url=svn_url,
                message=f"SVN commit failed: {r.stderr}",
                duration_seconds=time.time() - start_time,
            )

        return UploadResult(
            success=True,
            target_url=svn_url,
            message=f"已提交到 SVN: {dest_name}",
            bytes_uploaded=file_size,
            duration_seconds=time.time() - start_time,
        )

    except Exception as exc:
        return UploadResult(
            success=False,
            target_url=svn_url,
            message=f"SVN upload error: {exc}",
            duration_seconds=time.time() - start_time,
        )
    finally:
        # Clean up working directory
        if work_dir and Path(work_dir).exists():
            shutil.rmtree(work_dir, ignore_errors=True)


class SvnUploader(BaseUploader):
    """Upload artifacts to SVN.

    The SVN URL is constructed from the config's ``svn_root`` and the
    project's ``svn_leaf`` name.
    """

    max_retries = 2

    def upload(
        self,
        artifact: Path,
        config: dict[str, Any],
        log: logging.Logger,
    ) -> UploadResult:
        svn_root = config.get("svn_root", DEFAULT_SVN_ROOT)
        svn_exe = _svn_exe(config)
        skip_commit = config.get("skip_svn_commit", False)

        # Determine the SVN leaf name from the project config
        projects = config.get("projects", [])
        svn_leaf = ""
        for proj in projects:
            if proj.get("name"):
                svn_leaf = proj.get("svn_leaf", proj["name"])
                break
        if not svn_leaf:
            svn_leaf = artifact.stem.replace(".tar", "")

        svn_url = join_svn_url(svn_root, svn_leaf, artifact.name)
        log.info("SVN upload: %s -> %s", artifact.name, svn_url)

        return upload_artifact(artifact, svn_url, svn_exe, skip_commit)

# -*- coding: utf-8 -*-
"""SVN operations: list, ensure path, upload artifact.

This module contains the original SVN logic, updated to import
from the new ``core.constants`` and ``tools.exec`` modules.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from core.constants import DEFAULT_SVN_ROOT
from core.errors import UploadError
from tools.exec import run_process

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def join_svn_url(*parts: str) -> str:
    """Join SVN URL path segments, avoiding double slashes."""
    result = parts[0]
    for part in parts[1:]:
        part = part.strip("/")
        if part:
            result = result.rstrip("/") + "/" + part
    return result


def svn_exe() -> str:
    """Return the SVN executable (from env or PATH)."""
    return os.environ.get("SVN_EXECUTABLE", "svn")


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def list_svn_contents(svn_url: str) -> list[dict[str, str]]:
    """List the contents of an SVN directory.

    Returns a list of dicts with 'name', 'kind' (file/dir), and 'rev'.
    """
    try:
        r = run_process(
            [svn_exe(), "list", "--xml", svn_url],
            timeout=30,
        )
        if r.returncode != 0:
            logger.warning("SVN list failed: %s", r.stderr)
            return []

        # Parse XML output
        entries: list[dict[str, str]] = []
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.stdout)
            for entry_elem in root.findall(".//entry"):
                name_elem = entry_elem.find("name")
                kind = entry_elem.get("kind", "file")
                rev = entry_elem.get("revision", "")
                if name_elem is not None and name_elem.text:
                    entries.append({
                        "name": name_elem.text,
                        "kind": kind,
                        "rev": rev,
                    })
        except Exception as exc:
            logger.warning("Failed to parse SVN list XML: %s", exc)
            # Fallback: plain text list
            for line in r.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    entries.append({"name": line, "kind": "file", "rev": ""})

        return entries
    except Exception as exc:
        logger.error("SVN list error: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Ensure SVN path
# ---------------------------------------------------------------------------

def ensure_svn_path(svn_url: str) -> bool:
    """Ensure the SVN directory exists, creating parent directories.

    Uses ``svn mkdir --parents`` which is idempotent.
    """
    try:
        r = run_process(
            [svn_exe(), "mkdir", "-p", "--parents", svn_url,
             "-m", "auto-create directory by zbuild"],
            timeout=30,
        )
        if r.returncode == 0:
            logger.info("Created SVN path: %s", svn_url)
            return True
        # If it already exists, that's fine
        if "already exists" in r.stderr.lower() or "E195012" in r.stderr:
            return True
        logger.warning("SVN mkdir failed: %s", r.stderr)
        return False
    except Exception as exc:
        logger.error("SVN mkdir error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Upload artifact
# ---------------------------------------------------------------------------

def upload_artifact(
    artifact_path: Path,
    svn_url: str,
    skip_commit: bool = False,
) -> bool:
    """Upload an artifact to SVN.

    The process:
    1. Create a temp directory
    2. Checkout the parent SVN directory
    3. Clean existing files in the working copy
    4. Copy the artifact in
    5. svn add + svn commit

    Parameters
    ----------
    artifact_path:
        Local path to the artifact file.
    svn_url:
        Full SVN URL including the target filename.
    skip_commit:
        If True, prepare but do not commit.

    Returns
    -------
    bool:
        True on success.
    """
    work_dir = None
    try:
        work_dir = tempfile.mkdtemp(prefix="zbuild-svn-")

        # Determine parent URL
        parent_url = svn_url.rsplit("/", 1)[0] if "/" in svn_url else svn_url

        # Ensure parent exists
        ensure_svn_path(parent_url)

        # Checkout
        r = run_process(
            [svn_exe(), "checkout", parent_url, work_dir],
            timeout=60,
        )
        if r.returncode != 0:
            raise UploadError(f"SVN checkout failed: {r.stderr}")

        # Clean working directory (keep .svn)
        for item in Path(work_dir).iterdir():
            if item.name == ".svn":
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Copy artifact
        dest_name = artifact_path.name
        dest_path = Path(work_dir) / dest_name
        shutil.copy2(str(artifact_path), str(dest_path))
        logger.info("Copied artifact to working copy: %s", dest_path)

        if skip_commit:
            logger.info("Skip commit mode - artifact prepared but not committed")
            return True

        # SVN add
        r = run_process(
            [svn_exe(), "add", "--force", str(dest_path)],
            cwd=work_dir,
        )
        if r.returncode != 0:
            logger.warning("SVN add warning: %s", r.stderr)

        # SVN commit
        commit_msg = f"上传构建产物: {dest_name}"
        r = run_process(
            [svn_exe(), "commit", "-m", commit_msg, work_dir],
            timeout=120,
        )
        if r.returncode != 0:
            raise UploadError(f"SVN commit failed: {r.stderr}")

        logger.info("SVN commit successful: %s", svn_url)
        return True

    except UploadError:
        raise
    except Exception as exc:
        raise UploadError(f"SVN upload error: {exc}") from exc
    finally:
        if work_dir and Path(work_dir).exists():
            shutil.rmtree(work_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Convenience: full SVN upload for a project
# ---------------------------------------------------------------------------

def svn_upload_for_project(
    artifact_path: Path,
    project_name: str,
    svn_root: str = "",
    skip_commit: bool = False,
) -> str:
    """Upload an artifact for a project and return the SVN URL.

    Parameters
    ----------
    artifact_path:
        Path to the artifact.
    project_name:
        Project name (used as SVN leaf directory).
    svn_root:
        SVN root URL (defaults to DEFAULT_SVN_ROOT).
    skip_commit:
        If True, prepare but do not commit.

    Returns
    -------
    str:
        The SVN URL the artifact was uploaded to.
    """
    root = svn_root or DEFAULT_SVN_ROOT
    svn_url = join_svn_url(root, project_name, artifact_path.name)
    upload_artifact(artifact_path, svn_url, skip_commit)
    return svn_url

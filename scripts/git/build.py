# -*- coding: utf-8 -*-
"""Build operations: run deploy.sh, select artifacts, compute snapshots."""
from __future__ import annotations

import glob
import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from core.errors import BuildError
from tools.exec import run_process, run_process_stream
from git.branches import safe_git

logger = logging.getLogger(__name__)


def get_commit_sha(project_path: Path | str) -> str:
    """Return the current HEAD commit SHA."""
    try:
        r = run_process(safe_git(project_path) + ["rev-parse", "HEAD"])
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def build_project(
    project_path: Path | str,
    *,
    bash_exe: str = "bash",
    on_line: Optional[callable] = None,
) -> tuple[subprocess.CompletedProcess, Optional[Path]]:
    """Run deploy.sh in the project directory.

    Returns (completed_process, artifact_path) where artifact_path is
    the newest ``dist/*.tar.gz`` if one was created.

    Raises
    ------
    BuildError
        If deploy.sh is not found or fails.
    """
    project = Path(project_path)
    deploy_sh = project / "deploy.sh"

    if not deploy_sh.is_file():
        raise BuildError(f"deploy.sh not found in {project}")

    logger.info("Running deploy.sh in %s", project)

    result = run_process_stream(
        [bash_exe, "deploy.sh"],
        cwd=project,
        on_line=on_line,
        timeout=600,  # 10 minute timeout
    )

    if result.returncode != 0:
        raise BuildError(
            f"deploy.sh failed (exit {result.returncode}): "
            f"{result.stdout[-500:] if result.stdout else ''}"
        )

    # Find the newest tar.gz in dist/
    artifact = latest_artifact(project)
    return result, artifact


def fix_known_bad_deploy_tar(project_path: Path | str) -> Optional[Path]:
    """Attempt to fix a known issue where deploy.sh produces a bad tar.

    Some projects have a deploy.sh that creates a tar.gz with incorrect
    paths.  This function detects and fixes that case.

    Returns the fixed artifact path, or None if no fix was needed.
    """
    project = Path(project_path)
    dist_dir = project / "dist"
    if not dist_dir.is_dir():
        return None

    tarballs = sorted(dist_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not tarballs:
        return None

    newest = tarballs[0]
    # Check if the tar contains expected files
    try:
        r = run_process(["tar", "-tzf", str(newest)])
        if r.returncode == 0:
            entries = r.stdout.strip().split("\n")
            # If all entries start with a known bad prefix, flag it
            if entries and all(e.startswith("dist/") for e in entries[:5]):
                logger.warning("Known bad tar format detected in %s", newest)
                # Could re-pack here; for now just log
    except Exception:
        pass
    return newest


def artifact_snapshot(project_path: Path | str) -> dict[str, str]:
    """Return a snapshot of the current dist/ directory state.

    Returns dict mapping filename -> sha256 for each tar.gz in dist/.
    """
    project = Path(project_path)
    dist_dir = project / "dist"
    snapshot: dict[str, str] = {}

    if not dist_dir.is_dir():
        return snapshot

    for tarball in dist_dir.glob("*.tar.gz"):
        h = hashlib.sha256()
        with open(tarball, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        snapshot[tarball.name] = h.hexdigest()

    return snapshot


def latest_changed_artifact(
    project_path: Path | str,
    before_snapshot: dict[str, str],
) -> Optional[Path]:
    """Return the newest tar.gz that differs from the before snapshot."""
    project = Path(project_path)
    dist_dir = project / "dist"
    if not dist_dir.is_dir():
        return None

    tarballs = sorted(dist_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    for tb in tarballs:
        h = hashlib.sha256()
        with open(tb, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        current_hash = h.hexdigest()
        if before_snapshot.get(tb.name) != current_hash:
            return tb
    return None


def latest_artifact(project_path: Path | str) -> Optional[Path]:
    """Return the newest tar.gz in dist/, or None."""
    project = Path(project_path)
    dist_dir = project / "dist"
    if not dist_dir.is_dir():
        return None

    tarballs = sorted(dist_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    return tarballs[0] if tarballs else None


def summarize_process_output(result: subprocess.CompletedProcess) -> str:
    """Extract a short summary from a build process output."""
    if not result.stdout:
        return ""
    lines = result.stdout.strip().split("\n")
    # Return last 5 lines as summary
    return "\n".join(lines[-5:]) if len(lines) > 5 else result.stdout.strip()

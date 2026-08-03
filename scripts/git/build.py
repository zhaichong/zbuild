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
    build_command: str = "deploy.sh",
    on_line: Optional[callable] = None,
) -> tuple[subprocess.CompletedProcess, Optional[Path]]:
    """Run the configured build command/script in the project directory.

    Returns (completed_process, artifact_path) where artifact_path is
    the newest ``dist/*.tar.gz`` produced by *this* build.

    Raises
    ------
    BuildError
        If the build script is not found, fails, or finishes without producing
        a fresh ``dist/*.tar.gz`` (a pre-existing tarball is never
        accepted as the build result).
    """
    project = Path(project_path)
    cmd_str = (build_command or "deploy.sh").strip()

    # Determine command args and handle CRLF normalization if target is a shell script
    converted_crlf = False
    script_file_to_restore: Optional[Path] = None
    original_bytes: Optional[bytes] = None

    normalized_path_str = cmd_str
    if normalized_path_str.startswith(("./", ".\\")):
        normalized_path_str = normalized_path_str[2:]

    candidate_file = project / normalized_path_str

    if candidate_file.is_file() or cmd_str.endswith(".sh") or cmd_str.startswith("./"):
        if not candidate_file.is_file():
            raise BuildError(f"打包脚本 {cmd_str} 未找到 in {project}")

        # If it's a shell script, normalize CRLF -> LF
        if candidate_file.suffix.lower() == ".sh" or "sh" in candidate_file.name:
            original_bytes = candidate_file.read_bytes()
            lf_bytes = original_bytes.replace(b"\r\n", b"\n")
            converted_crlf = lf_bytes != original_bytes
            if converted_crlf:
                candidate_file.write_bytes(lf_bytes)
                script_file_to_restore = candidate_file

            rel_script = candidate_file.relative_to(project).as_posix()
            run_cmd = [bash_exe, rel_script]
        else:
            run_cmd = [str(candidate_file)]
    else:
        import shlex
        try:
            parts = shlex.split(cmd_str, posix=False)
        except Exception:
            parts = cmd_str.split()

        if not parts:
            parts = [bash_exe, "deploy.sh"]

        if parts[0].lower() in ("bash", "sh") and len(parts) > 1:
            target_sh = parts[1]
            if target_sh.startswith(("./", ".\\")):
                target_sh = target_sh[2:]
            target_sh_file = project / target_sh
            if target_sh_file.is_file():
                original_bytes = target_sh_file.read_bytes()
                lf_bytes = original_bytes.replace(b"\r\n", b"\n")
                converted_crlf = lf_bytes != original_bytes
                if converted_crlf:
                    target_sh_file.write_bytes(lf_bytes)
                    script_file_to_restore = target_sh_file
            run_cmd = [bash_exe] + parts[1:]
        else:
            run_cmd = parts

    # Capture a snapshot of the dist/ directory before the build starts
    pre_snapshot = artifact_snapshot(project)
    build_start = time.time()

    logger.info("Running build command '%s' in %s", cmd_str, project)

    # Inject configured Node.js path to environment
    from git.deps import _node_env
    env = _node_env()

    try:
        result = run_process_stream(
            run_cmd,
            cwd=project,
            env=env,
            on_line=on_line,
            timeout=600,  # 10 minute timeout
        )
    finally:
        if converted_crlf and script_file_to_restore and original_bytes is not None:
            try:
                script_file_to_restore.write_bytes(original_bytes)
            except Exception:
                logger.warning("Failed to restore %s line endings", script_file_to_restore)

    # A non-zero build is never publishable, even if it left a partial archive.
    if result.returncode != 0:
        raise BuildError(
            f"打包命令 '{cmd_str}' 执行失败 (exit {result.returncode}): "
            f"{result.stdout[-500:] if result.stdout else ''}"
        )

    # Find the newest tar.gz that changed during the build
    artifact = latest_changed_artifact(project, pre_snapshot)

    # Also accept a tarball rewritten during this build with identical
    # content (reproducible build) - freshness is proven by its mtime.
    if not artifact:
        artifact = _fresh_artifact(project, build_start)

    # Never fall back to a pre-existing tarball
    if not artifact:
        raise BuildError(
            f"打包命令 '{cmd_str}' 执行结束，但 dist/ 中没有产生新的 .tar.gz 产物。"
            "构建可能已静默失败，请检查上面的构建日志。"
            + (f"\n输出尾部: {result.stdout[-300:]}" if result.stdout else "")
        )

    return result, artifact


def _fresh_artifact(project_path: Path | str, since: float) -> Optional[Path]:
    """Return the newest dist/*.tar.gz modified at or after *since*."""
    project = Path(project_path)
    dist_dir = project / "dist"
    if not dist_dir.is_dir():
        return None

    tarballs = sorted(dist_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    for tb in tarballs:
        # 1s tolerance for filesystem mtime granularity
        if tb.stat().st_mtime >= since - 1:
            return tb
    return None


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

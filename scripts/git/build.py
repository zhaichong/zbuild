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


def resolve_candidate_dirs(
    project_path: Path | str,
    candidate_paths: list[str] | str | None = None,
) -> list[Path]:
    """Return list of candidate output directory Paths for a project.

    `candidate_paths` can be a list of relative strings (e.g. ['dist', 'build', 'target'])
    or a comma/semicolon separated string ('dist, build, target').
    Defaults to ['dist'] if empty or None.
    """
    project = Path(project_path)
    if candidate_paths is None:
        raw_list = ["dist"]
    elif isinstance(candidate_paths, str):
        raw_list = [p.strip() for p in candidate_paths.replace(";", ",").split(",") if p.strip()]
    else:
        raw_list = [str(p).strip() for p in candidate_paths if str(p).strip()]

    if not raw_list:
        raw_list = ["dist"]

    dirs = []
    for rel_p in raw_list:
        p = project / rel_p
        dirs.append(p)
    return dirs


def _find_all_tarballs(
    project_path: Path | str,
    candidate_paths: list[str] | str | None = None,
) -> list[Path]:
    """Find all tarballs / zip files in candidate output directories."""
    project = Path(project_path)
    dirs = resolve_candidate_dirs(project, candidate_paths)
    found: list[Path] = []
    seen: set[Path] = set()

    for d in dirs:
        if d.is_dir():
            for ext in ("*.tar.gz", "*.tgz", "*.tar", "*.zip"):
                for tb in d.glob(ext):
                    if tb not in seen:
                        seen.add(tb)
                        found.append(tb)
        elif d.is_file() and d.suffix.lower() in (".gz", ".tgz", ".tar", ".zip"):
            if d not in seen:
                seen.add(d)
                found.append(d)

    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def build_project(
    project_path: Path | str,
    *,
    bash_exe: str = "bash",
    build_command: str = "deploy.sh",
    artifact_paths: list[str] | str | None = None,
    on_line: Optional[callable] = None,
) -> tuple[subprocess.CompletedProcess, Optional[Path]]:
    """Run the configured build command/script in the project directory.

    Returns (completed_process, artifact_path) where artifact_path is
    the newest tarball produced by *this* build in the candidate search paths.
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

    # Capture a snapshot of candidate directories before the build starts
    pre_snapshot = artifact_snapshot(project, candidate_paths=artifact_paths)
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
    artifact = latest_changed_artifact(project, pre_snapshot, candidate_paths=artifact_paths)

    # Also accept a tarball rewritten during this build with identical
    # content (reproducible build) - freshness is proven by its mtime.
    if not artifact:
        artifact = _fresh_artifact(project, build_start, candidate_paths=artifact_paths)

    # Never fall back to a pre-existing tarball
    if not artifact:
        searched_dirs = ", ".join(str(p.relative_to(project) if p.is_relative_to(project) else p.name) for p in resolve_candidate_dirs(project, artifact_paths))
        raise BuildError(
            f"打包命令 '{cmd_str}' 执行结束，但在搜索路径 [{searched_dirs}] 中没有产生新的压缩包 (.tar.gz / .zip)。"
            "构建可能已静默失败，请检查上面的构建日志。"
            + (f"\n输出尾部: {result.stdout[-300:]}" if result.stdout else "")
        )

    return result, artifact


def _fresh_artifact(
    project_path: Path | str,
    since: float,
    candidate_paths: list[str] | str | None = None,
) -> Optional[Path]:
    """Return the newest tarball modified at or after *since*."""
    tarballs = _find_all_tarballs(project_path, candidate_paths)
    for tb in tarballs:
        # 1s tolerance for filesystem mtime granularity
        if tb.stat().st_mtime >= since - 1:
            return tb
    return None


def fix_known_bad_deploy_tar(
    project_path: Path | str,
    candidate_paths: list[str] | str | None = None,
) -> Optional[Path]:
    """Attempt to fix a known issue where deploy.sh produces a bad tar."""
    tarballs = _find_all_tarballs(project_path, candidate_paths)
    if not tarballs:
        return None

    newest = tarballs[0]
    # Check if the tar contains expected files
    try:
        r = run_process(["tar", "-tzf", str(newest)])
        if r.returncode == 0:
            entries = r.stdout.strip().split("\n")
            if entries and all(e.startswith("dist/") for e in entries[:5]):
                logger.warning("Known bad tar format detected in %s", newest)
    except Exception:
        pass
    return newest


def artifact_snapshot(
    project_path: Path | str,
    candidate_paths: list[str] | str | None = None,
) -> dict[str, str]:
    """Return a snapshot of tarballs in candidate directories.

    Returns dict mapping relative_filepath -> sha256.
    """
    project = Path(project_path)
    tarballs = _find_all_tarballs(project, candidate_paths)
    snapshot: dict[str, str] = {}

    for tarball in tarballs:
        h = hashlib.sha256()
        with open(tarball, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        rel_key = str(tarball.relative_to(project)) if tarball.is_relative_to(project) else tarball.name
        snapshot[rel_key] = h.hexdigest()

    return snapshot


def latest_changed_artifact(
    project_path: Path | str,
    before_snapshot: dict[str, str],
    candidate_paths: list[str] | str | None = None,
) -> Optional[Path]:
    """Return the newest tarball across candidate dirs that differs from before_snapshot."""
    project = Path(project_path)
    tarballs = _find_all_tarballs(project, candidate_paths)

    for tb in tarballs:
        h = hashlib.sha256()
        with open(tb, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        current_hash = h.hexdigest()
        rel_key = str(tb.relative_to(project)) if tb.is_relative_to(project) else tb.name
        if before_snapshot.get(rel_key) != current_hash:
            return tb
    return None


def latest_artifact(
    project_path: Path | str,
    candidate_paths: list[str] | str | None = None,
) -> Optional[Path]:
    """Return the newest tarball across candidate output directories, or None."""
    tarballs = _find_all_tarballs(project_path, candidate_paths)
    return tarballs[0] if tarballs else None


def summarize_process_output(result: subprocess.CompletedProcess) -> str:
    """Extract a short summary from a build process output."""
    if not result.stdout:
        return ""
    lines = result.stdout.strip().split("\n")
    # Return last 5 lines as summary
    return "\n".join(lines[-5:]) if len(lines) > 5 else result.stdout.strip()

# -*- coding: utf-8 -*-
"""Build operations: run deploy.sh, select artifacts, compute snapshots."""

import glob
import hashlib
import logging
import re
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.errors import BuildError
from git.build_cmd import resolve_run_argv
from tools.exec import run_process, run_process_stream
from git.branches import safe_git

logger = logging.getLogger(__name__)

_TAR_MISSING_PATH = re.compile(r"^tar: .+: Cannot stat: No such file or directory$")
_TAR_FAILURE_SUMMARY = "tar: Exiting with failure status due to previous errors"


def get_commit_sha(project_path: Union[Path, str]) -> str:
    """Return the current HEAD commit SHA."""
    try:
        r = run_process(safe_git(project_path) + ["rev-parse", "HEAD"])
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def resolve_candidate_dirs(
    project_path: Union[Path, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
) -> List[Path]:
    """Return list of candidate output directory Paths for a project.

    `candidate_paths` can be a list of relative strings (e.g. ['dist', 'build', 'target'])
    or a comma/semicolon separated string ('dist, build, target, output, .').
    Defaults to ['dist', 'release', 'build', 'output', 'target'] if empty or None.
    """
    project = Path(project_path)
    default_dirs = ["dist", "release", "build", "output", "target"]

    if candidate_paths is None:
        raw_list = default_dirs
    elif isinstance(candidate_paths, str):
        raw_list = [p.strip() for p in candidate_paths.replace(";", ",").split(",") if p.strip()]
    else:
        raw_list = []
        for item in candidate_paths:
            if isinstance(item, str):
                raw_list.extend([p.strip() for p in item.replace(";", ",").split(",") if p.strip()])
            elif item:
                raw_list.append(str(item).strip())

    if not raw_list:
        raw_list = default_dirs

    dirs = []
    for rel_p in raw_list:
        if "*" in rel_p or "?" in rel_p:
            matched = [p for p in project.glob(rel_p) if p.is_dir()]
            if matched:
                dirs.extend(matched)
            else:
                dirs.append(project / rel_p)
        else:
            dirs.append(project / rel_p)
    return dirs


def _find_all_tarballs(
    project_path: Union[Path, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
) -> List[Path]:
    """Find all tarballs / zip files in candidate output directories and subdirectories."""
    project = Path(project_path)
    dirs = resolve_candidate_dirs(project, candidate_paths)
    found: List[Path] = []
    seen: Set[Path] = set()

    for d in dirs:
        if d.is_dir():
            for ext in ("*.tar.gz", "*.tgz", "*.tar", "*.zip"):
                # 1. 搜寻当前产物目录直下产物
                for tb in d.glob(ext):
                    if tb not in seen:
                        seen.add(tb)
                        found.append(tb)
                # 2. 搜寻分支独立子目录产物 (支持如 dist/branch_name/*.tar.gz)
                for tb in d.glob(f"*/{ext}"):
                    if tb not in seen:
                        seen.add(tb)
                        found.append(tb)
                for tb in d.glob(f"*/*/{ext}"):
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
    project_path: Union[Path, str],
    *,
    bash_exe: str = "bash",
    build_command: str = "deploy.sh",
    target_branch: str = "",
    artifact_paths: Union[List[str], Optional[str]] = None,
    on_line: Optional[callable] = None,
) -> Tuple[subprocess.CompletedProcess, Optional[Path]]:
    """Run the configured build command/script in the project directory.

    Returns (completed_process, artifact_path) where artifact_path is
    the newest tarball produced by *this* build in the candidate search paths.
    """
    project = Path(project_path)
    run_cmd, cmd_str = resolve_run_argv(project, build_command, bash_exe=bash_exe)

    # Normalize CRLF -> LF for shell scripts under the project (Windows checkouts)
    converted_crlf = False
    script_file_to_restore: Optional[Path] = None
    original_bytes: Optional[bytes] = None

    script_token = None
    if len(run_cmd) >= 2 and Path(str(run_cmd[0]).replace("\\", "/")).name.lower().startswith(
        ("bash", "sh")
    ):
        script_token = next((a for a in run_cmd[1:] if not str(a).startswith("-")), None)
    elif len(run_cmd) == 1 and str(run_cmd[0]).lower().endswith((".sh", ".bash")):
        script_token = run_cmd[0]

    # Legacy deploy scripts use their first positional argument for the
    # release label. Worktrees are detached by design, so asking Git inside
    # the script would otherwise yield "(HEAD detached at ...)".
    if script_token and target_branch:
        run_cmd.append(target_branch)

    if script_token:
        script_path = Path(script_token)
        if not script_path.is_absolute():
            script_path = project / script_path
        if script_path.is_file() and (
            script_path.suffix.lower() in {".sh", ".bash"} or "sh" in script_path.name.lower()
        ):
            original_bytes = script_path.read_bytes()
            lf_bytes = original_bytes.replace(b"\r\n", b"\n")
            converted_crlf = lf_bytes != original_bytes
            if converted_crlf:
                script_path.write_bytes(lf_bytes)
                script_file_to_restore = script_path

    # Capture a snapshot of candidate directories before the build starts
    pre_snapshot = artifact_snapshot(project, candidate_paths=artifact_paths)
    build_start = time.time()

    logger.info("Running build command '%s' in %s", " ".join(run_cmd), project)

    # Use the same Node 14 shims and isolated npm prefix as dependency install.
    # deploy.sh runs under Bash and otherwise resolves Volta/system Node first.
    from git.deps import _node_env
    env = _node_env()
    if target_branch:
        env["BRANCH_NAME"] = str(target_branch)
        env["BUILD_BRANCH"] = str(target_branch)
        env["GIT_BRANCH"] = str(target_branch)

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

    if result.returncode != 0:
        artifact = latest_changed_artifact(project, pre_snapshot, candidate_paths=artifact_paths)
        if not artifact:
            artifact = _fresh_artifact(project, build_start, candidate_paths=artifact_paths)
        if is_ignorable_tar_stat_failure(result, artifact):
            logger.info(
                "Ignoring known non-fatal tar missing-path error; verified artifact: %s",
                artifact,
            )
            return result, artifact

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


def is_ignorable_tar_stat_failure(
    result: subprocess.CompletedProcess, artifact: Optional[Path]
) -> bool:
    """Accept one legacy tar missing-path error only after archive validation."""
    if result.returncode == 0 or not artifact or not artifact.is_file():
        return False

    tar_lines = [
        line.strip()
        for line in (result.stdout or "").splitlines()
        if line.lstrip().startswith("tar:")
    ]
    if len(tar_lines) != 2 or not _TAR_MISSING_PATH.fullmatch(tar_lines[0]):
        return False
    if tar_lines[1] != _TAR_FAILURE_SUMMARY:
        return False

    try:
        with tarfile.open(artifact, "r:*") as archive:
            return bool(archive.getmembers())
    except (OSError, tarfile.TarError):
        return False


def _fresh_artifact(
    project_path: Union[Path, str],
    since: float,
    candidate_paths: Union[List[str], Optional[str]] = None,
) -> Optional[Path]:
    """Return the newest tarball modified at or after *since*."""
    tarballs = _find_all_tarballs(project_path, candidate_paths)
    for tb in tarballs:
        # 1s tolerance for filesystem mtime granularity
        if tb.stat().st_mtime >= since - 1:
            return tb
    return None


def fix_known_bad_deploy_tar(
    project_path: Union[Path, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
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
    project_path: Union[Path, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
) -> Dict[str, str]:
    """Return a snapshot of tarballs in candidate directories.

    Returns dict mapping relative_filepath -> sha256.
    """
    project = Path(project_path)
    tarballs = _find_all_tarballs(project, candidate_paths)
    snapshot: Dict[str, str] = {}

    for tarball in tarballs:
        h = hashlib.sha256()
        with open(tarball, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        rel_key = str(tarball.relative_to(project)) if tarball.is_relative_to(project) else tarball.name
        snapshot[rel_key] = h.hexdigest()

    return snapshot


def latest_changed_artifact(
    project_path: Union[Path, str],
    before_snapshot: Dict[str, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
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
    project_path: Union[Path, str],
    candidate_paths: Union[List[str], Optional[str]] = None,
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

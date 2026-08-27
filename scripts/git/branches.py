# -*- coding: utf-8 -*-
"""Git branch operations.

All functions accept a project path and use the system ``git`` command
(or the bundled version) to query and manipulate branches.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from core.errors import GitError
from tools.exec import run_process

logger = logging.getLogger(__name__)


def safe_git(project_path: Union[Path, str]) -> List[str]:
    """Return the base git command list for the given project.

    Uses ``git`` from PATH; callers can override by setting GIT_EXECUTABLE.
    """
    import os
    git_exe = os.environ.get("GIT_EXECUTABLE", "git")
    return [git_exe, "-C", str(project_path)]


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def read_current_branch(project_path: Union[Path, str]) -> str:
    """Return the current branch name, or empty string on failure."""
    try:
        r = run_process(
            safe_git(project_path) + ["rev-parse", "--abbrev-ref", "HEAD"],
        )
        if r.returncode == 0:
            branch = r.stdout.strip()
            if branch != "HEAD":
                return branch
    except Exception:
        pass
    return ""


def _normalize_branch_name(raw_branch: str) -> Optional[str]:
    """Strip git remote prefixes (origin/, remotes/origin/, remotes/upstream/, etc.)
    properly while preserving multi-segment branch names like 'feature/v1/login'.
    """
    if not isinstance(raw_branch, str):
        return None
    b = raw_branch.strip()
    if not b or b == "HEAD" or b.endswith("/HEAD"):
        return None

    # Strip 'remotes/' if present
    if b.startswith("remotes/"):
        b = b[len("remotes/"):]

    # Strip known or generic remote prefix (e.g. 'origin/foo' -> 'foo')
    if "/" in b:
        first_segment, rest = b.split("/", 1)
        if first_segment in {"origin", "upstream", "remote", "remotes"} or not rest.startswith("heads/"):
            b = rest

    # Strip 'heads/' if left over from ref name formatting
    if b.startswith("heads/"):
        b = b[len("heads/"):]

    b = b.strip()
    return b if b else None


def read_branches(project_path: Union[Path, str]) -> List[str]:
    """Return all local and cached remote tracking branch names without remote prefix."""
    try:
        r = run_process(
            safe_git(project_path) + ["branch", "-a", "--list", "--format=%(refname:short)"],
        )
        if r.returncode == 0:
            seen = set()
            branches = []
            for b in r.stdout.strip().split("\n"):
                normalized = _normalize_branch_name(b)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    branches.append(normalized)
            return branches
    except Exception as exc:
        logger.debug("Failed to read branches for %s: %s", project_path, exc)
    return []


def fetch_remote_branches(project_path: Union[Path, str]) -> List[str]:
    """Fetch from origin and return remote branch names (without origin/ prefix)."""
    try:
        r = run_process(
            safe_git(project_path) + ["fetch", "--prune", "origin"],
            timeout=30,
        )
        if r.returncode != 0:
            logger.warning("git fetch failed: %s", r.stderr)
    except Exception as exc:
        logger.warning("git fetch error: %s", exc)

    try:
        r = run_process(
            safe_git(project_path) + ["branch", "-r", "--list", "--format=%(refname:short)"],
        )
        if r.returncode == 0:
            seen = set()
            branches = []
            for line in r.stdout.strip().split("\n"):
                normalized = _normalize_branch_name(line)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    branches.append(normalized)
            return branches
    except Exception as exc:
        logger.debug("Failed to fetch remote branches for %s: %s", project_path, exc)
    return []


def refresh_project_branches(project_path: Union[Path, str]) -> List[str]:
    """Fetch remote branches and return combined local + remote branch list."""
    local = read_branches(project_path)
    remote = fetch_remote_branches(project_path)
    combined = list(dict.fromkeys(local + remote))  # deduplicate, preserve order
    return combined


# ---------------------------------------------------------------------------
# Local changes detection
# ---------------------------------------------------------------------------

def local_changes(project_path: Union[Path, str]) -> Dict[str, List[str]]:
    """Return a dict with 'staged', 'unstaged', and 'untracked' file lists."""
    result: Dict[str, List[str]] = {"staged": [], "unstaged": [], "untracked": []}
    try:
        r = run_process(
            safe_git(project_path) + ["status", "--porcelain"],
        )
        if r.returncode != 0:
            return result

        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            status = line[:2]
            filepath = line[3:].strip()
            if status == "??":
                result["untracked"].append(filepath)
            elif status[0] != " ":
                result["staged"].append(filepath)
            elif status[1] != " ":
                result["unstaged"].append(filepath)
    except Exception:
        pass
    return result


def local_changes_summary(project_path: Union[Path, str]) -> dict:
    """Return a summary dict with has_changes flag and counts."""
    changes = local_changes(project_path)
    has_changes = bool(changes["staged"] or changes["unstaged"] or changes["untracked"])
    return {
        "has_changes": has_changes,
        "staged_count": len(changes["staged"]),
        "unstaged_count": len(changes["unstaged"]),
        "untracked_count": len(changes["untracked"]),
        "staged": changes["staged"],
        "unstaged": changes["unstaged"],
        "untracked": changes["untracked"],
    }


# ---------------------------------------------------------------------------
# Stash / branch switching
# ---------------------------------------------------------------------------

def stash_local_changes(project_path: Union[Path, str]) -> Union[dict, bool]:
    """Stash any local changes (including untracked files).

    Returns a stash record dict with details, or False if nothing to stash.
    """
    changes = local_changes(project_path)
    all_files = changes["staged"] + changes["unstaged"] + changes["untracked"]
    if not all_files:
        return False
    try:
        r = run_process(
            safe_git(project_path) + ["stash", "push", "--include-untracked", "-m", "zbuild-auto-stash"],
        )
        if r.returncode == 0:
            return {
                "stashed": True,
                "message": "zbuild-auto-stash",
                "file_count": len(all_files),
                "files": all_files[:12],
            }
        return False
    except Exception:
        return False


def ensure_branch(
    project_path: Union[Path, str],
    target_branch: str,
    allow_stash: bool = True,
) -> Union[dict, bool]:
    """Switch to *target_branch*, fetching remote first and stashing if needed.

    Parameters
    ----------
    project_path:
        Path to the git repository.
    target_branch:
        Branch name to switch to.
    allow_stash:
        If True (default), local changes are stashed before switching.
        If False and there are local changes, returns a dict with
        ``blocked=True`` and the changed file list.

    Returns True on success, a stash record dict if stash was created,
    or a dict with ``blocked=True`` if local changes block the switch.
    """
    # Check for local changes first
    changes = local_changes(project_path)
    all_files = changes["staged"] + changes["unstaged"] + changes["untracked"]
    has_local_changes = bool(all_files)

    # If not allowed to stash and there are changes, block
    if has_local_changes and not allow_stash:
        return {
            "blocked": True,
            "files": all_files[:20],
            "file_count": len(all_files),
        }

    # Stash local changes if any (including untracked)
    stash_record = None
    if has_local_changes:
        stash_record = stash_local_changes(project_path)
        if not stash_record:
            return False

    current = read_current_branch(project_path)
    if current == target_branch:
        return stash_record if stash_record else True

    # Fetch remote branches first to ensure new branches are visible
    fetch_remote_branches(project_path)

    try:
        # Try local checkout first
        r = run_process(
            safe_git(project_path) + ["checkout", target_branch],
        )
        if r.returncode == 0:
            if isinstance(stash_record, dict):
                return stash_record
            return True

        # Try creating from remote tracking branch
        r = run_process(
            safe_git(project_path) + ["checkout", "-b", target_branch, f"origin/{target_branch}"],
        )
        if r.returncode == 0:
            if isinstance(stash_record, dict):
                return stash_record
            return True

        logger.error("Failed to switch to branch %s: %s", target_branch, r.stderr)
        # Restore stashed changes before giving up so the working tree is clean
        if stash_record and isinstance(stash_record, dict) and stash_record.get("stashed"):
            run_process(safe_git(project_path) + ["stash", "pop"])
        return False
    except Exception as exc:
        logger.error("Branch switch error: %s", exc)
        # Restore stashed changes on exception too
        if stash_record and isinstance(stash_record, dict) and stash_record.get("stashed"):
            try:
                run_process(safe_git(project_path) + ["stash", "pop"])
            except Exception:
                logger.warning("Failed to pop stash after error")
        return False

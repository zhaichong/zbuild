# -*- coding: utf-8 -*-
"""Git branch operations.

All functions accept a project path and use the system ``git`` command
(or the bundled version) to query and manipulate branches.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from core.errors import GitError
from tools.exec import run_process

logger = logging.getLogger(__name__)


def safe_git(project_path: Path | str) -> list[str]:
    """Return the base git command list for the given project.

    Uses ``git`` from PATH; callers can override by setting GIT_EXECUTABLE.
    """
    import os
    git_exe = os.environ.get("GIT_EXECUTABLE", "git")
    return [git_exe, "-C", str(project_path)]


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def read_current_branch(project_path: Path | str) -> str:
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


def read_branches(project_path: Path | str) -> list[str]:
    """Return all local branch names."""
    try:
        r = run_process(
            safe_git(project_path) + ["branch", "--list", "--format=%(refname:short)"],
        )
        if r.returncode == 0:
            return [b.strip() for b in r.stdout.strip().split("\n") if b.strip()]
    except Exception:
        pass
    return []


def fetch_remote_branches(project_path: Path | str) -> list[str]:
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
            branches = []
            for line in r.stdout.strip().split("\n"):
                line = line.strip()
                if line and not line.endswith("/HEAD"):
                    # Remove "origin/" prefix
                    if "/" in line:
                        line = line.split("/", 1)[1]
                    branches.append(line)
            return branches
    except Exception:
        pass
    return []


def refresh_project_branches(project_path: Path | str) -> list[str]:
    """Fetch remote branches and return combined local + remote branch list."""
    local = read_branches(project_path)
    remote = fetch_remote_branches(project_path)
    combined = list(dict.fromkeys(local + remote))  # deduplicate, preserve order
    return combined


# ---------------------------------------------------------------------------
# Local changes detection
# ---------------------------------------------------------------------------

def local_changes(project_path: Path | str) -> dict[str, list[str]]:
    """Return a dict with 'staged', 'unstaged', and 'untracked' file lists."""
    result: dict[str, list[str]] = {"staged": [], "unstaged": [], "untracked": []}
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
            elif status[0] in ("M", "A", "D", "R"):
                result["staged"].append(filepath)
            elif status[1] in ("M", "D"):
                result["unstaged"].append(filepath)
    except Exception:
        pass
    return result


def local_changes_summary(project_path: Path | str) -> dict:
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

def stash_local_changes(project_path: Path | str) -> bool:
    """Stash any local changes. Returns True if stash was created."""
    changes = local_changes(project_path)
    if not changes["staged"] and not changes["unstaged"]:
        return False
    try:
        r = run_process(
            safe_git(project_path) + ["stash", "push", "-m", "zbuild-auto-stash"],
        )
        return r.returncode == 0
    except Exception:
        return False


def ensure_branch(project_path: Path | str, target_branch: str) -> bool:
    """Switch to *target_branch*, creating it from origin if needed.

    Returns True on success.
    """
    current = read_current_branch(project_path)
    if current == target_branch:
        return True

    # Stash local changes if any
    stashed = stash_local_changes(project_path)

    try:
        # Try local checkout first
        r = run_process(
            safe_git(project_path) + ["checkout", target_branch],
        )
        if r.returncode == 0:
            return True

        # Try creating from remote tracking branch
        r = run_process(
            safe_git(project_path) + ["checkout", "-b", target_branch, f"origin/{target_branch}"],
        )
        if r.returncode == 0:
            return True

        logger.error("Failed to switch to branch %s: %s", target_branch, r.stderr)
        return False
    except Exception as exc:
        logger.error("Branch switch error: %s", exc)
        return False

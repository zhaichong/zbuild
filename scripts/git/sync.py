# -*- coding: utf-8 -*-
"""Git sync operations: pull latest, commit info."""

import logging
import subprocess
from pathlib import Path

from tools.exec import run_process
from git.branches import safe_git
from typing import Dict, Tuple, Union

logger = logging.getLogger(__name__)


def pull_latest(project_path: Union[Path, str]) -> Tuple[bool, str]:
    """Pull the latest code for the current branch.

    If there are local uncommitted changes (e.g. vue.config.js modified by
    deploy.sh), they are automatically stashed before the pull and restored
    afterwards so that the rebase does not fail.

    Returns (success, message).
    """
    git = safe_git(project_path)
    stashed = False

    try:
        # Check for unstaged / staged changes
        status_r = run_process(git + ["status", "--porcelain"], timeout=10)
        if status_r.returncode == 0 and status_r.stdout.strip():
            # There are local modifications – stash them first
            stash_r = run_process(
                git + ["stash", "push", "-u", "-m", "zbuild-auto-stash"],
                timeout=30,
            )
            if stash_r.returncode == 0 and "No local changes" not in stash_r.stdout:
                stashed = True
                logger.debug("Auto-stashed local changes before pull: %s", stash_r.stdout.strip())

        r = run_process(
            git + ["pull", "--rebase"],
            timeout=60,
        )
        if r.returncode == 0:
            output = r.stdout.strip()
            if stashed:
                # Restore stashed changes
                pop_r = run_process(git + ["stash", "pop"], timeout=30)
                if pop_r.returncode != 0:
                    logger.warning("Failed to restore stash: %s", pop_r.stderr.strip())
            if "Already up to date" in output:
                return True, "Already up to date"
            return True, output
        else:
            err = r.stderr.strip() or r.stdout.strip()
            if stashed:
                # Try to restore even on failure
                run_process(git + ["stash", "pop"], timeout=30)
            return False, err
    except subprocess.TimeoutExpired:
        return False, "Pull timed out after 60 seconds"
    except Exception as exc:
        return False, str(exc)



def latest_commit_info(project_path: Union[Path, str]) -> Dict[str, str]:
    """Return info about the latest commit.

    Returns dict with keys: sha, author, date, message.
    """
    info: Dict[str, str] = {"sha": "", "author": "", "date": "", "message": ""}
    try:
        r = run_process(
            safe_git(project_path) + [
                "log", "-1", "--format=%H%n%an%n%ai%n%s"
            ],
        )
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 4:
                info["sha"] = lines[0]
                info["author"] = lines[1]
                info["date"] = lines[2]
                info["message"] = lines[3]
            elif len(lines) >= 1:
                info["sha"] = lines[0]
    except Exception:
        pass
    return info

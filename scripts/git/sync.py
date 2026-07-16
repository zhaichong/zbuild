# -*- coding: utf-8 -*-
"""Git sync operations: pull latest, commit info."""
from __future__ import annotations

import logging
from pathlib import Path

from tools.exec import run_process
from git.branches import safe_git

logger = logging.getLogger(__name__)


def pull_latest(project_path: Path | str) -> tuple[bool, str]:
    """Pull the latest code for the current branch.

    Returns (success, message).
    """
    try:
        r = run_process(
            safe_git(project_path) + ["pull", "--rebase"],
            timeout=60,
        )
        if r.returncode == 0:
            output = r.stdout.strip()
            if "Already up to date" in output:
                return True, "Already up to date"
            return True, output
        else:
            return False, r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Pull timed out after 60 seconds"
    except Exception as exc:
        return False, str(exc)


def latest_commit_info(project_path: Path | str) -> dict[str, str]:
    """Return info about the latest commit.

    Returns dict with keys: sha, author, date, message.
    """
    info: dict[str, str] = {"sha": "", "author": "", "date": "", "message": ""}
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


# Need subprocess for TimeoutExpired
import subprocess

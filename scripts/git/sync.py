# -*- coding: utf-8 -*-
"""Git sync operations: pull latest, commit info."""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from tools.exec import run_process
from git.branches import safe_git

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



MICRO_FRONTEND_SIBLINGS = frozenset({"yarward-micro-menu", "yarward-nova-ai"})


def sync_micro_frontend_siblings(
    project_path: Union[Path, str],
    target_branch: str = "",
    on_line: Optional[callable] = None,
) -> None:
    """Detect and synchronize sibling micro-frontend repositories (e.g. yarward-micro-menu, yarward-nova-ai).

    When packaging a parent project (like yarward-web-frontend), legacy scripts (e.g. deploy-micro.sh)
    switch directory to `../yarward-micro-menu` and `../yarward-nova-ai` to build sub-bundles.
    This function ensures those sibling repos are fetched and updated to the latest commits
    matching the target branch (or their active branch) before the build begins.
    """
    project = Path(project_path).resolve()
    parent_dir = project.parent
    if not parent_dir.is_dir():
        return

    for sibling_name in MICRO_FRONTEND_SIBLINGS:
        sibling_dir = parent_dir / sibling_name
        if not (sibling_dir / ".git").exists():
            continue

        git = safe_git(sibling_dir)
        if on_line:
            on_line(f"🔄 正在同步微前端依赖工程最新代码: {sibling_name} ...")
        logger.info("Synchronizing sibling micro-frontend repo: %s (target_branch=%s)", sibling_dir, target_branch)

        try:
            # 1. Stash any uncommitted modifications in sibling repo
            stashed = False
            status_r = run_process(git + ["status", "--porcelain"], timeout=10)
            if status_r.returncode == 0 and status_r.stdout.strip():
                stash_r = run_process(git + ["stash", "push", "-u", "-m", "zbuild-auto-stash"], timeout=30)
                if stash_r.returncode == 0 and "No local changes" not in stash_r.stdout:
                    stashed = True

            # 2. Fetch remote updates
            run_process(git + ["fetch", "--prune", "origin"], timeout=60)

            # 3. Check if target branch exists on origin (e.g. 3.5.0)
            branch_to_use = ""
            if target_branch:
                chk = run_process(git + ["rev-parse", "--verify", f"origin/{target_branch}"], timeout=10)
                if chk.returncode == 0:
                    branch_to_use = target_branch

            if branch_to_use:
                # Switch and pull target branch
                run_process(git + ["checkout", branch_to_use], timeout=30)
                pull_r = run_process(git + ["pull", "--rebase"], timeout=60)
                if on_line:
                    on_line(f"✔ 微前端工程 {sibling_name} 已对齐最新分支 {branch_to_use}")
            else:
                # Pull current active branch
                pull_r = run_process(git + ["pull", "--rebase"], timeout=60)
                if on_line:
                    on_line(f"✔ 微前端工程 {sibling_name} 已更新至最新代码")

            # 4. Restore stash if needed
            if stashed:
                run_process(git + ["stash", "pop"], timeout=30)

        except Exception as exc:
            logger.warning("Failed to auto-sync sibling repo %s: %s", sibling_name, exc)
            if on_line:
                on_line(f"⚠️ 微前端工程 {sibling_name} 自动同步跳过: {exc}")

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

# -*- coding: utf-8 -*-
"""Affected-projects detection (Nx-style).

Uses ``git diff`` to find changed files and maps them back to
projects to determine which ones need rebuilding.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from tools.exec import run_process
from git.branches import safe_git

logger = logging.getLogger(__name__)


def _changed_files(
    project_path: Path | str,
    base_ref: str = "main",
    head_ref: str = "HEAD",
) -> list[str]:
    """Return list of files changed between two refs."""
    try:
        r = run_process(
            safe_git(project_path) + ["diff", "--name-only", base_ref, head_ref],
        )
        if r.returncode == 0:
            return [f.strip() for f in r.stdout.strip().split("\n") if f.strip()]
    except Exception:
        pass
    return []


def _map_file_to_project(
    file_path: str,
    project_dirs: dict[str, Path],
) -> Optional[str]:
    """Map a changed file path to its owning project name.

    Parameters
    ----------
    file_path:
        Relative path of the changed file (from the repo root).
    project_dirs:
        Mapping of project name -> project directory path.
    """
    for name, pdir in project_dirs.items():
        # Check if the file is inside this project directory
        try:
            Path(file_path).relative_to(pdir.name)
            return name
        except ValueError:
            continue
    return None


def find_affected_projects(
    repo_path: Path | str,
    project_dirs: dict[str, Path],
    base_ref: str = "main",
    head_ref: str = "HEAD",
) -> list[str]:
    """Find projects affected by changes between two refs.

    Parameters
    ----------
    repo_path:
        Path to the Git repository root.
    project_dirs:
        Mapping of project name -> project directory path (relative to repo).
    base_ref:
        The base Git ref to compare against (default: "main").
    head_ref:
        The head Git ref (default: "HEAD").

    Returns
    -------
    list[str]:
        Names of affected projects.
    """
    changed = _changed_files(repo_path, base_ref, head_ref)
    if not changed:
        logger.info("No changes detected between %s and %s", base_ref, head_ref)
        return []

    affected: set[str] = set()
    for f in changed:
        project_name = _map_file_to_project(f, project_dirs)
        if project_name:
            affected.add(project_name)
        else:
            # If a file cannot be mapped, it might be a shared file
            # that affects all projects
            logger.debug("Unmapped changed file: %s", f)
            # Check if it is a shared config (package.json at root, etc.)
            if f in ("package.json", "pnpm-lock.yaml", "yarn.lock",
                     "package-lock.json", "nx.json", "tsconfig.base.json"):
                logger.info("Shared file %s changed, marking all projects affected", f)
                affected.update(project_dirs.keys())

    result = sorted(affected)
    logger.info("Affected projects: %s", result)
    return result


def find_affected_projects_from_staged(
    repo_path: Path | str,
    project_dirs: dict[str, Path],
) -> list[str]:
    """Find projects affected by staged (uncommitted) changes."""
    try:
        r = run_process(
            safe_git(repo_path) + ["diff", "--name-only", "--cached"],
        )
        if r.returncode != 0:
            return []
        changed = [f.strip() for f in r.stdout.strip().split("\n") if f.strip()]
    except Exception:
        return []

    affected: set[str] = set()
    for f in changed:
        project_name = _map_file_to_project(f, project_dirs)
        if project_name:
            affected.add(project_name)

    return sorted(affected)

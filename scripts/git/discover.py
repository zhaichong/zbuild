# -*- coding: utf-8 -*-
"""Project discovery.

Scans configured directories for Git repositories and builds
``ProjectInfo`` objects with branch metadata.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from core.constants import ProjectInfo, PROJECT_DEFAULTS_PATH
from core.config import load_json
from git.branches import read_current_branch, read_branches

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project defaults mapping
# ---------------------------------------------------------------------------

def _load_project_defaults() -> dict[str, dict]:
    """Load the project-defaults.json mapping.

    Returns a dict keyed by project directory name, with values like::

        {"default_svn_leaf": "zhbf-bedhead-frontend", ...}
    """
    if not PROJECT_DEFAULTS_PATH.exists():
        return {}
    data = load_json(PROJECT_DEFAULTS_PATH, default={})
    if isinstance(data, dict):
        return data
    return {}


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_projects(
    search_dirs: Optional[list[str]] = None,
) -> list[ProjectInfo]:
    """Discover Git projects in the given directories.

    Parameters
    ----------
    search_dirs:
        List of directory paths to scan.  Each immediate subdirectory
        that contains a ``.git`` folder is treated as a project.
        If empty, returns an empty list.

    Returns
    -------
    list[ProjectInfo]:
        Discovered projects with branch metadata populated.
    """
    if not search_dirs:
        return []

    defaults = _load_project_defaults()
    projects: list[ProjectInfo] = []

    for search_dir in search_dirs:
        base = Path(search_dir)
        if not base.is_dir():
            logger.warning("Search directory does not exist: %s", base)
            continue

        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            git_dir = child / ".git"
            if not git_dir.exists():
                continue

            name = child.name
            current_branch = read_current_branch(child)
            all_branches = read_branches(child)
            default_svn_leaf = defaults.get(name, {}).get("default_svn_leaf", name)

            projects.append(ProjectInfo(
                name=name,
                path=child,
                current_branch=current_branch,
                branches=all_branches,
                default_svn_leaf=default_svn_leaf,
            ))
            logger.debug("Discovered project: %s at %s (branch=%s)", name, child, current_branch)

    return projects


def discover_single(project_path: str) -> Optional[ProjectInfo]:
    """Discover a single project by path.

    Returns None if the path is not a valid Git repository.
    """
    p = Path(project_path)
    if not (p / ".git").exists():
        return None

    defaults = _load_project_defaults()
    name = p.name
    current_branch = read_current_branch(p)
    all_branches = read_branches(p)
    default_svn_leaf = defaults.get(name, {}).get("default_svn_leaf", name)

    return ProjectInfo(
        name=name,
        path=p,
        current_branch=current_branch,
        branches=all_branches,
        default_svn_leaf=default_svn_leaf,
    )

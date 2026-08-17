# -*- coding: utf-8 -*-
"""Project discovery.

Scans configured directories for Git repositories and builds
``ProjectInfo`` objects with branch metadata.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from core.constants import (
    ProjectInfo,
    PROJECT_DEFAULTS_PATH,
    DEFAULT_BUILD_COMMAND,
    DEFAULT_BUILD_COMMANDS,
    DEFAULT_SERVER_UPLOAD_PATHS,
)
from core.config import load_json
from git.branches import read_current_branch, read_branches
from git.build_cmd import detect_project_build_command

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project defaults mapping
# ---------------------------------------------------------------------------

def _load_project_defaults() -> Dict[str, dict]:
    """Load the project-defaults.json mapping.

    Returns a dict keyed by project directory name, with values like::

        {"defaultSvnLeaf": "zhbf-bedhead-frontend", "serverUploadPath": "/home/data/web", "buildCommand": "deploy.sh"}
    """
    if not PROJECT_DEFAULTS_PATH.exists():
        return {}
    data = load_json(PROJECT_DEFAULTS_PATH, default=[])
    if isinstance(data, list):
        return {
            item["projectName"]: item
            for item in data
            if isinstance(item, dict) and "projectName" in item
        }
    if isinstance(data, dict):
        return data
    return {}


def _resolve_build_command(project_path: Path, raw_build_cmd: str) -> str:
    """Resolve build command, auto-detecting package.json scripts if default script is missing."""
    cmd = (raw_build_cmd or DEFAULT_BUILD_COMMAND).strip()
    if cmd == DEFAULT_BUILD_COMMAND and not (project_path / "deploy.sh").is_file():
        detected = detect_project_build_command(project_path)
        if detected:
            return " ".join(detected)
    return cmd


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_projects(
    search_dirs: Optional[List[str]] = None,
) -> List[ProjectInfo]:
    """Discover Git projects in the given directories.

    Parameters
    ----------
    search_dirs:
        List of directory paths to scan. If empty/None, returns empty list.
    """
    if not search_dirs:
        return []

    defaults = _load_project_defaults()
    projects: List[ProjectInfo] = []

    for search_dir in search_dirs:
        base = Path(search_dir)
        if not base.is_dir():
            logger.warning("Search directory does not exist: %s", base)
            continue

        # If search_dir itself is a Git repository, discover it directly
        if (base / ".git").exists():
            name = base.name
            current_branch = read_current_branch(base)
            all_branches = read_branches(base)
            proj_default = defaults.get(name, {})
            default_svn_leaf = proj_default.get("defaultSvnLeaf") or proj_default.get("default_svn_leaf", name)
            svn_root = proj_default.get("svnRoot") or proj_default.get("svn_root", "")
            server_upload_path = proj_default.get("serverUploadPath") or proj_default.get("server_upload_path") or DEFAULT_SERVER_UPLOAD_PATHS.get(name, "")
            raw_build_command = proj_default.get("buildCommand") or proj_default.get("build_command") or DEFAULT_BUILD_COMMANDS.get(name, DEFAULT_BUILD_COMMAND)
            build_command = _resolve_build_command(base, raw_build_command)

            projects.append(ProjectInfo(
                name=name,
                path=base,
                current_branch=current_branch,
                branches=all_branches,
                default_svn_leaf=default_svn_leaf,
                svn_root=svn_root,
                server_upload_path=server_upload_path,
                build_command=build_command,
            ))
            logger.debug("Discovered root project: %s at %s (branch=%s)", name, base, current_branch)

        # Also scan subdirectories for mono-repo / sub-project packages
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name == ".git":
                continue
            git_dir = child / ".git"
            if not git_dir.exists():
                continue

            name = child.name
            current_branch = read_current_branch(child)
            all_branches = read_branches(child)
            proj_default = defaults.get(name, {})
            default_svn_leaf = proj_default.get("defaultSvnLeaf") or proj_default.get("default_svn_leaf", name)
            svn_root = proj_default.get("svnRoot") or proj_default.get("svn_root", "")
            server_upload_path = proj_default.get("serverUploadPath") or proj_default.get("server_upload_path") or DEFAULT_SERVER_UPLOAD_PATHS.get(name, "")
            raw_build_command = proj_default.get("buildCommand") or proj_default.get("build_command") or DEFAULT_BUILD_COMMANDS.get(name, DEFAULT_BUILD_COMMAND)
            build_command = _resolve_build_command(child, raw_build_command)

            projects.append(ProjectInfo(
                name=name,
                path=child,
                current_branch=current_branch,
                branches=all_branches,
                default_svn_leaf=default_svn_leaf,
                svn_root=svn_root,
                server_upload_path=server_upload_path,
                build_command=build_command,
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
    proj_default = defaults.get(name, {})
    default_svn_leaf = proj_default.get("defaultSvnLeaf") or proj_default.get("default_svn_leaf", name)
    server_upload_path = proj_default.get("serverUploadPath") or proj_default.get("server_upload_path") or DEFAULT_SERVER_UPLOAD_PATHS.get(name, "")
    build_command = proj_default.get("buildCommand") or proj_default.get("build_command") or DEFAULT_BUILD_COMMANDS.get(name, DEFAULT_BUILD_COMMAND)

    return ProjectInfo(
        name=name,
        path=p,
        current_branch=current_branch,
        branches=all_branches,
        default_svn_leaf=default_svn_leaf,
        server_upload_path=server_upload_path,
        build_command=build_command,
    )

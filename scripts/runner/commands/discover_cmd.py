# -*- coding: utf-8 -*-
"""Commands: discover, refresh-branches, check-local-changes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from runner.cli import register
from git.discover import discover_projects
from git.branches import refresh_project_branches, local_changes_summary, read_current_branch


@register("discover")
def cmd_discover(payload: dict[str, Any]) -> dict[str, Any]:
    """Discover all configured projects and return their metadata."""
    root_path = payload.get("rootPath", "")
    if not root_path:
        return {"success": False, "error": "Missing 'rootPath'", "projects": []}
    search_dirs = [root_path]
    projects = discover_projects(search_dirs)
    return {
        "success": True,
        "projects": [
            {
                "name": p.name,
                "path": str(p.path),
                "current_branch": p.current_branch,
                "branches": p.branches,
                "default_svn_leaf": p.default_svn_leaf,
                "server_upload_path": p.server_upload_path,
                "build_command": p.build_command,
            }
            for p in projects
        ],
    }


@register("refresh-branches")
def cmd_refresh_branches(payload: dict[str, Any]) -> dict[str, Any]:
    """Refresh the branch list for a specific project."""
    project_path = payload.get("repoPath", "")
    if not project_path:
        return {"success": False, "error": "Missing 'repoPath'"}

    try:
        branches = refresh_project_branches(project_path)
        current = read_current_branch(project_path)
        return {"success": True, "branches": branches, "current_branch": current}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@register("check-local-changes")
def cmd_check_local_changes(payload: dict[str, Any]) -> dict[str, Any]:
    """Check for uncommitted local changes across projects."""
    projects = payload.get("projects", [])
    if not projects:
        return {"success": True, "changes": []}

    results = []
    for proj in projects:
        name = proj.get("project", "")
        branch = proj.get("branch", "")
        root_path = payload.get("rootPath", "")
        # Build the full project path
        project_path = proj.get("path", "")
        if not project_path and root_path and name:
            project_path = str(Path(root_path) / name)
        if not project_path:
            continue
        summary = local_changes_summary(project_path)
        summary["project"] = name
        summary["branch"] = branch
        results.append(summary)

    return {"success": True, "changes": results}

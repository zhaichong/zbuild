# -*- coding: utf-8 -*-
"""Commands: discover, refresh-branches, check-local-changes."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from git.discover import discover_projects
from git.branches import refresh_project_branches, local_changes_summary


@register("discover")
def cmd_discover(payload: dict[str, Any]) -> dict[str, Any]:
    """Discover all configured projects and return their metadata."""
    search_dirs = payload.get("search_dirs", [])
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
            }
            for p in projects
        ],
    }


@register("refresh-branches")
def cmd_refresh_branches(payload: dict[str, Any]) -> dict[str, Any]:
    """Refresh the branch list for a specific project."""
    project_path = payload.get("project_path", "")
    if not project_path:
        return {"success": False, "error": "Missing 'project_path'"}

    try:
        branches = refresh_project_branches(project_path)
        return {"success": True, "branches": branches}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@register("check-local-changes")
def cmd_check_local_changes(payload: dict[str, Any]) -> dict[str, Any]:
    """Check for uncommitted local changes in a project."""
    project_path = payload.get("project_path", "")
    if not project_path:
        return {"success": False, "error": "Missing 'project_path'"}

    summary = local_changes_summary(project_path)
    return {"success": True, "has_changes": summary["has_changes"], "summary": summary}

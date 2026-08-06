# -*- coding: utf-8 -*-
"""Commands: detect affected projects based on git changes."""

from pathlib import Path
from typing import Any, Dict

from runner.cli import register
from git.affected import find_affected_projects, find_affected_projects_from_staged


@register("detect-affected")
def cmd_detect_affected(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Detect projects affected by changes between git refs.

    Parameters
    ----------
    payload : dict
        repo_path: Path to the git repository root
        search_dirs: List of directories to search for projects
        base_ref: Base git ref to compare against (default: "main")
        head_ref: Head git ref (default: "HEAD")
    """
    repo_path = payload.get("repoPath") or payload.get("repo_path", "")
    search_dirs = payload.get("searchDirs") or payload.get("search_dirs", [])
    base_ref = payload.get("baseRef") or payload.get("base_ref", "main")
    head_ref = payload.get("headRef") or payload.get("head_ref", "HEAD")

    if not repo_path:
        return {"success": False, "error": "Missing 'repo_path'"}

    # Discover projects to build the project_dirs mapping
    from git.discover import discover_projects
    projects = discover_projects(search_dirs)

    # Build project_dirs mapping: project_name -> relative path from repo
    repo = Path(repo_path).resolve()
    project_dirs = {}
    for p in projects:
        try:
            p_path = Path(p.path).resolve()
            if p_path == repo:
                project_dirs[p.name] = Path(".")
            else:
                rel_path = p_path.relative_to(repo)
                project_dirs[p.name] = rel_path
        except ValueError:
            # Fallback using os.path.relpath for cross-drive or case differences on Windows
            try:
                import os
                rel = os.path.relpath(str(p_path), str(repo))
                if not rel.startswith(".."):
                    project_dirs[p.name] = Path(rel)
            except Exception:
                continue

    affected = find_affected_projects(repo_path, project_dirs, base_ref, head_ref)

    return {
        "success": True,
        "affected_projects": affected,
        "base_ref": base_ref,
        "head_ref": head_ref,
    }


@register("detect-affected-staged")
def cmd_detect_affected_staged(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Detect projects affected by staged (uncommitted) changes.

    Parameters
    ----------
    payload : dict
        repo_path: Path to the git repository root
        search_dirs: List of directories to search for projects
    """
    repo_path = payload.get("repoPath") or payload.get("repo_path", "")
    search_dirs = payload.get("searchDirs") or payload.get("search_dirs", [])

    if not repo_path:
        return {"success": False, "error": "Missing 'repo_path'"}

    # Discover projects to build the project_dirs mapping
    from git.discover import discover_projects
    projects = discover_projects(search_dirs)

    # Build project_dirs mapping
    repo = Path(repo_path).resolve()
    project_dirs = {}
    for p in projects:
        try:
            p_path = Path(p.path).resolve()
            if p_path == repo:
                project_dirs[p.name] = Path(".")
            else:
                rel_path = p_path.relative_to(repo)
                project_dirs[p.name] = rel_path
        except ValueError:
            try:
                import os
                rel = os.path.relpath(str(p_path), str(repo))
                if not rel.startswith(".."):
                    project_dirs[p.name] = Path(rel)
            except Exception:
                continue

    affected = find_affected_projects_from_staged(repo_path, project_dirs)

    return {
        "success": True,
        "affected_projects": affected,
    }

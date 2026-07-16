# -*- coding: utf-8 -*-
"""Command: svn-list."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from svn_ops import list_svn_contents


@register("svn-list")
def cmd_svn_list(payload: dict[str, Any]) -> dict[str, Any]:
    """List contents of an SVN directory."""
    svn_url = payload.get("svn_url", "")
    if not svn_url:
        return {"success": False, "error": "Missing 'svn_url'"}

    try:
        entries = list_svn_contents(svn_url)
        return {"success": True, "entries": entries}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

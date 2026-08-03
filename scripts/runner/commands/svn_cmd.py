# -*- coding: utf-8 -*-
"""Command: svn-list."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from uploaders.svn import list_svn_contents


@register("svn-list")
def cmd_svn_list(payload: dict[str, Any]) -> dict[str, Any]:
    """List contents of an SVN directory."""
    svn_root = payload.get("svn", "")
    url_path = payload.get("url", "")
    # Construct full URL: if url is already absolute, use it; otherwise join with svn root
    if url_path.startswith("http") or url_path.startswith("svn://"):
        svn_url = url_path
    elif svn_root and url_path:
        svn_url = svn_root.rstrip("/") + "/" + url_path.lstrip("/")
    elif url_path:
        svn_url = url_path
    else:
        svn_url = svn_root

    if not svn_url:
        return {"success": False, "error": "Missing 'svn' or 'url'"}

    # Accept credentials from flat fields (frontend) or nested svn_credentials
    username = payload.get("username", "")
    password = payload.get("password", "")
    if not username:
        svn_creds = payload.get("svn_credentials", {})
        username = svn_creds.get("username", "")
        password = svn_creds.get("password", "")

    try:
        entries = list_svn_contents(svn_url, username=username, password=password)
        return {"success": True, "entries": entries}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

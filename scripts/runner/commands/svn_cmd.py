# -*- coding: utf-8 -*-
"""Command: svn-list."""

from typing import Any, Dict

from runner.cli import register
from uploaders.svn import list_svn_contents


@register("svn-list")
def cmd_svn_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List contents of an SVN directory."""
    svn_exe = payload.get("svn", "") or payload.get("svn_exe", "") or "svn"
    url_path = payload.get("url", "")
    svn_root = payload.get("svn_root", "") or payload.get("svnRootUrl", "")

    # Construct full URL
    import urllib.parse
    if url_path:
        url_path = urllib.parse.unquote(str(url_path))

    if url_path.lower().startswith(("http://", "https://", "svn://", "file://")):
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
        entries = list_svn_contents(
            svn_url=svn_url,
            svn_exe=svn_exe,
            username=username,
            password=password,
        )
        return {"success": True, "entries": entries}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

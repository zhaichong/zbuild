# -*- coding: utf-8 -*-
"""Command: detect-tools."""

from typing import Any, Dict

from runner.cli import register
from tools.detect import detect_tools


@register("detect-tools")
def cmd_detect_tools(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Detect all required external tools and return their status."""
    # Frontend may send Partial<AppConfig> with {tools: {git, bash, svn}}
    # or legacy {extra_paths: [...]} format.
    # Pass the full payload as config so detect_tools can extract
    # user-configured tool paths via config.get("tools", {}).
    # Also extract any extra_paths (directories) for fallback search.
    extra_paths = payload.get("extra_paths") or payload.get("extraPaths") or []
    tools = detect_tools(config=payload, extra_paths=extra_paths)
    return {"success": True, "tools": tools}

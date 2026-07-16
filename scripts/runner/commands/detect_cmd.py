# -*- coding: utf-8 -*-
"""Command: detect-tools."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from tools.detect import detect_tools


@register("detect-tools")
def cmd_detect_tools(payload: dict[str, Any]) -> dict[str, Any]:
    """Detect all required external tools and return their status."""
    extra_paths = payload.get("extra_paths")
    tools = detect_tools(extra_paths)
    return {"success": True, "tools": tools}

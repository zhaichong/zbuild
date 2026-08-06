# -*- coding: utf-8 -*-
"""Apply configured tool paths into the process environment.

Electron may launch with a minimal PATH (no Git/Bash). Discover and other
commands receive ``tools`` from the frontend config, but historically ignored
them — so ``git branch`` failed silently and the UI showed empty branches.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _tool_path(tools: Any, name: str) -> str:
    """Extract a tool path from frontend or detect-tools shapes."""
    if not isinstance(tools, dict):
        return ""
    value = tools.get(name, "")
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        path = value.get("path") or ""
        return str(path).strip() if path else ""
    return ""


def apply_tools_env(payload: Optional[Dict[str, Any]] = None, *, config: Optional[Dict[str, Any]] = None) -> None:
    """Set GIT_EXECUTABLE / PATH from payload tools (or auto-detect fallback).

    Safe to call multiple times; only sets values when a usable path is found.
    """
    tools: Dict[str, Any] = {}
    if isinstance(payload, dict):
        raw = payload.get("tools")
        if isinstance(raw, dict):
            tools = raw
        # Nested config (run payload)
        cfg = payload.get("config")
        if isinstance(cfg, dict) and isinstance(cfg.get("tools"), dict):
            for k, v in cfg["tools"].items():
                if k not in tools or not _tool_path(tools, k):
                    tools[k] = v
    if isinstance(config, dict) and isinstance(config.get("tools"), dict):
        for k, v in config["tools"].items():
            if k not in tools or not _tool_path(tools, k):
                tools[k] = v

    git_path = _tool_path(tools, "git")
    bash_path = _tool_path(tools, "bash")
    node_path = _tool_path(tools, "node")

    # Fall back to detection / bundled when not provided
    if not git_path or not Path(git_path).is_file():
        try:
            from tools.bundled import bundled_git
            from tools.detect import find_tool

            git_path = bundled_git() or find_tool("git") or git_path
        except Exception as exc:
            logger.debug("git fallback lookup failed: %s", exc)

    if git_path and Path(git_path).is_file():
        os.environ["GIT_EXECUTABLE"] = git_path
        git_dir = str(Path(git_path).parent)
        _prepend_path(git_dir)
        # Git for Windows often keeps bash next to git
        if not bash_path:
            try:
                from tools.detect import bash_from_git

                bash_path = bash_from_git(git_path) or ""
            except Exception:
                pass
        logger.debug("GIT_EXECUTABLE=%s", git_path)
    else:
        logger.warning("Git executable not resolved; branch queries may return empty")

    if bash_path and Path(bash_path).is_file():
        os.environ["BASH_EXECUTABLE"] = bash_path
        _prepend_path(str(Path(bash_path).parent))

    if node_path and Path(node_path).is_file():
        _prepend_path(str(Path(node_path).parent))


def _prepend_path(directory: str) -> None:
    if not directory:
        return
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    if directory in parts:
        return
    # Case-insensitive check on Windows
    if os.name == "nt":
        low = directory.lower()
        if any(p.lower() == low for p in parts):
            return
    os.environ["PATH"] = directory + os.pathsep + current if current else directory

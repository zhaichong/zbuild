# -*- coding: utf-8 -*-
"""Tool detection and validation utilities.

Consolidated from the original process.py and electron_runner.py
detection logic.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from tools.exec import run_process

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def command_exists(name: str) -> bool:
    """Return True if *name* can be found on PATH."""
    return shutil.which(name) is not None


def validate_executable(path: str | Path) -> bool:
    """Return True if *path* points to an existing executable file."""
    p = Path(path)
    if not p.is_file():
        return False
    # On Windows, any .exe / .cmd / .bat is executable
    if os.name == "nt":
        return p.suffix.lower() in (".exe", ".cmd", ".bat", ".com", "")
    return os.access(p, os.X_OK)


def find_tool(name: str, extra_paths: Optional[list[str | Path]] = None) -> Optional[str]:
    """Locate an executable by name, searching *extra_paths* first.

    Returns the full path as a string, or None if not found.
    """
    # Search extra paths first
    if extra_paths:
        for d in extra_paths:
            candidate = Path(d) / name
            if os.name == "nt":
                for ext in (".exe", ".cmd", ".bat", ""):
                    c = candidate.with_suffix(ext) if ext else candidate
                    if c.is_file():
                        return str(c)
            elif candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)

    # Fall back to system PATH
    found = shutil.which(name)
    return found


def bash_from_git(git_path: str) -> Optional[str]:
    """Derive the bash executable bundled alongside Git for Windows.

    Given a git.exe path like ``C:\\Program Files\\Git\\cmd\\git.exe``,
    this returns ``C:\\Program Files\\Git\\bin\\bash.exe``.
    """
    git = Path(git_path)
    # Typical layout: <root>/cmd/git.exe -> <root>/bin/bash.exe
    bash_candidate = git.parent.parent / "bin" / "bash.exe"
    if bash_candidate.is_file():
        return str(bash_candidate)
    # Alternative: <root>/usr/bin/bash.exe
    alt = git.parent.parent / "usr" / "bin" / "bash.exe"
    if alt.is_file():
        return str(alt)
    return None


# ---------------------------------------------------------------------------
# High-level detection
# ---------------------------------------------------------------------------

def detect_tools(
    extra_paths: Optional[list[str | Path]] = None,
) -> dict[str, Any]:
    """Detect all required external tools and return a status dict.

    Returns a dictionary with keys: git, bash, svn, node, npm, npx.
    Each value is a dict with ``path`` (str or None) and ``version`` (str or None).
    """
    result: dict[str, Any] = {}

    # --- Git ---
    git_path = find_tool("git", extra_paths)
    git_version = None
    if git_path:
        try:
            r = run_process([git_path, "--version"])
            git_version = r.stdout.strip()
        except Exception:
            pass
    result["git"] = {"path": git_path, "version": git_version}

    # --- Bash (prefer Git-bundled bash on Windows) ---
    bash_path = None
    if git_path:
        bash_path = bash_from_git(git_path)
    if not bash_path:
        bash_path = find_tool("bash", extra_paths)
    bash_version = None
    if bash_path:
        try:
            r = run_process([bash_path, "--version"])
            bash_version = r.stdout.strip().split("\n")[0]
        except Exception:
            pass
    result["bash"] = {"path": bash_path, "version": bash_version}

    # --- SVN ---
    svn_path = find_tool("svn", extra_paths)
    svn_version = None
    if svn_path:
        try:
            r = run_process([svn_path, "--version", "--quiet"])
            svn_version = r.stdout.strip()
        except Exception:
            pass
    result["svn"] = {"path": svn_path, "version": svn_version}

    # --- Node ---
    node_path = find_tool("node", extra_paths)
    node_version = None
    if node_path:
        try:
            r = run_process([node_path, "--version"])
            node_version = r.stdout.strip()
        except Exception:
            pass
    result["node"] = {"path": node_path, "version": node_version}

    # --- npm ---
    npm_path = find_tool("npm", extra_paths)
    npm_version = None
    if npm_path:
        try:
            r = run_process([npm_path, "--version"])
            npm_version = r.stdout.strip()
        except Exception:
            pass
    result["npm"] = {"path": npm_path, "version": npm_version}

    # --- npx ---
    npx_path = find_tool("npx", extra_paths)
    result["npx"] = {"path": npx_path, "version": None}

    return result

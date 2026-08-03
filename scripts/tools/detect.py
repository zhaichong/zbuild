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


def validate_executable(path: str | Path, expected_name: str = "") -> tuple[bool, str]:
    """Return (ok, message) if *path* points to a working executable.

    Checks file existence, optionally verifies the name matches, and
    runs --version to confirm the tool works.
    """
    p = Path(path)
    if not p.is_file():
        return False, f"路径不存在: {path}"
    if os.name == "nt" and p.suffix.lower() not in (".exe", ".cmd", ".bat", ".com", ""):
        return False, f"不是可执行文件: {path}"
    if os.name != "nt" and not os.access(p, os.X_OK):
        return False, f"无执行权限: {path}"
    # Optionally verify the executable name matches
    if expected_name:
        stem = p.stem.lower()
        if expected_name.lower() not in stem and stem not in expected_name.lower():
            return False, f"文件名不匹配: 期望 {expected_name}, 实际 {p.name}"
    # Run --version to verify the executable actually works
    try:
        r = run_process([str(p), "--version"], timeout=10)
        if r.returncode == 0:
            return True, f"OK: {r.stdout.strip().split(chr(10))[0][:60]}"
        return False, f"--version 返回非零 (exit {r.returncode}): {r.stderr[:100]}"
    except Exception as exc:
        return False, f"运行 --version 失败: {exc}"


# Windows candidate paths for common tool installations
_WINDOWS_CANDIDATES: dict[str, list[str]] = {
    "git": [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"D:\application\Git\cmd\git.exe",
        r"D:\application\Git\bin\git.exe",
    ],
    "bash": [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"D:\application\Git\bin\bash.exe",
        r"D:\application\Git\usr\bin\bash.exe",
    ],
    "svn": [
        r"C:\Program Files\SlikSvn\bin\svn.exe",
        r"C:\Program Files (x86)\SlikSvn\bin\svn.exe",
        r"C:\Program Files\TortoiseSVN\bin\svn.exe",
        r"D:\application\SlikSvn\bin\svn.exe",
    ],
    "node": [
        r"C:\Program Files\nodejs\node.exe",
        r"D:\application\nodejs\node.exe",
    ],
    "npm": [
        r"C:\Program Files\nodejs\npm.cmd",
        r"D:\application\nodejs\npm.cmd",
    ],
}


def find_tool(
    name: str,
    extra_paths: Optional[list[str | Path]] = None,
    configured_path: str = "",
) -> Optional[str]:
    """Locate an executable by name.

    Search order: configured_path > extra_paths > Windows candidates > PATH.
    Returns the full path as a string, or None if not found.
    """
    # 1. User-configured path from settings
    if configured_path:
        p = Path(configured_path)
        if p.is_file():
            return str(p)
        # If configured as a directory, look inside
        if p.is_dir():
            candidate = p / name
            if os.name == "nt":
                for ext in (".exe", ".cmd", ".bat", ""):
                    c = candidate.with_suffix(ext) if ext else candidate
                    if c.is_file():
                        return str(c)
            elif candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)

    # 2. Extra paths
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

    # 3. Hardcoded Windows candidate paths
    if os.name == "nt":
        for candidate in _WINDOWS_CANDIDATES.get(name, []):
            if Path(candidate).is_file():
                return candidate

    # 4. System PATH
    found = shutil.which(name)
    return found


def bash_from_git(git_path: str) -> Optional[str]:
    """Derive the bash executable bundled alongside Git for Windows.

    Given a git.exe path like ``C:\\Program Files\\Git\\cmd\\git.exe``,
    this returns ``C:\\Program Files\\Git\\bin\\bash.exe``.
    """
    git = Path(git_path)
    candidates = [
        git.parent / "bash.exe",
        git.parent / "usr" / "bin" / "bash.exe",
        git.parent.parent / "bin" / "bash.exe",
        git.parent.parent / "usr" / "bin" / "bash.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


# ---------------------------------------------------------------------------
# High-level detection
# ---------------------------------------------------------------------------

def detect_tools(
    config: Optional[dict[str, Any]] = None,
    extra_paths: Optional[list[str | Path]] = None,
) -> dict[str, Any]:
    """Detect all required external tools and return a status dict.

    Parameters
    ----------
    config:
        Configuration dict. If it contains a ``tools`` sub-dict with
        ``git``/``bash``/``svn`` keys, those user-configured paths are
        tried first before auto-detection.
    extra_paths:
        Additional directories to search.

    Returns a dictionary with keys: git, bash, svn, node, npm, npx.
    Each value is a dict with ``path`` (str or None) and ``version`` (str or None).
    """
    result: dict[str, Any] = {}

    # Extract user-configured tool paths from config
    cfg_tools = (config or {}).get("tools", {}) if isinstance(config, dict) else {}
    git_cfg = cfg_tools.get("git", "") if isinstance(cfg_tools, dict) else ""
    bash_cfg = cfg_tools.get("bash", "") if isinstance(cfg_tools, dict) else ""
    svn_cfg = cfg_tools.get("svn", "") if isinstance(cfg_tools, dict) else ""
    node_cfg = cfg_tools.get("node", "") if isinstance(cfg_tools, dict) else ""
    npm_cfg = cfg_tools.get("npm", "") if isinstance(cfg_tools, dict) else ""

    # --- Git ---
    git_path = find_tool("git", extra_paths, configured_path=git_cfg)
    git_version = None
    if git_path:
        try:
            r = run_process([git_path, "--version"], timeout=10)
            git_version = r.stdout.strip()
        except Exception:
            pass
    result["git"] = {"path": git_path, "version": git_version}

    # --- Bash (prefer user-configured bash, fallback to Git-bundled bash on Windows) ---
    bash_path = None
    if bash_cfg:
        bash_path = find_tool("bash", extra_paths, configured_path=bash_cfg)
    if not bash_path and git_path:
        bash_path = bash_from_git(git_path)
    if not bash_path:
        bash_path = find_tool("bash", extra_paths)
    bash_version = None
    if bash_path:
        try:
            r = run_process([bash_path, "--version"], timeout=10)
            bash_version = r.stdout.strip().split("\n")[0]
        except Exception:
            pass
    result["bash"] = {"path": bash_path, "version": bash_version}

    # --- SVN ---
    svn_path = find_tool("svn", extra_paths, configured_path=svn_cfg)
    svn_version = None
    if svn_path:
        try:
            r = run_process([svn_path, "--version", "--quiet"], timeout=10)
            svn_version = r.stdout.strip()
        except Exception:
            pass
    result["svn"] = {"path": svn_path, "version": svn_version}

    # --- Node (Prioritize Node.js 14) ---
    from tools.bundled import bundled_node, bundled_npm, bundled_npx
    node_path = node_cfg or bundled_node() or find_tool("node", extra_paths)
    node_version = None
    if node_path:
        try:
            r = run_process([node_path, "--version"], timeout=10)
            node_version = r.stdout.strip()
        except Exception:
            pass
    result["node"] = {"path": node_path, "version": node_version}

    # --- npm ---
    npm_path = npm_cfg or bundled_npm() or find_tool("npm", extra_paths)
    npm_version = None
    if npm_path:
        try:
            r = run_process([npm_path, "--version"], timeout=10)
            npm_version = r.stdout.strip()
        except Exception:
            pass
    result["npm"] = {"path": npm_path, "version": npm_version}

    # --- npx ---
    npx_path = bundled_npx()
    if not npx_path and node_path:
        npx_exe = "npx.cmd" if os.name == "nt" else "npx"
        npx_cand = Path(node_path).parent / npx_exe
        if npx_cand.is_file():
            npx_path = str(npx_cand)
    if not npx_path:
        npx_path = find_tool("npx", extra_paths)
    result["npx"] = {"path": npx_path, "version": None}

    return result

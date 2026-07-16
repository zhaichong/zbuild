# -*- coding: utf-8 -*-
"""Bundled tool path resolution.

Provides paths to bundled runtimes (Python, Git, Bash, SVN, Node, npm)
that ship alongside the Electron application, and helpers to set up
shims so that child processes pick up the bundled versions.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

from core.constants import APP_DIR
from tools.exec import run_process

logger = logging.getLogger(__name__)

REQUIRED_NODE_VERSION = "14.21.3"

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------

def runtime_root() -> Path:
    """Return the root directory for bundled runtimes.

    In a packaged Electron app this is ``resources/runtime/``;
    during development it falls back to ``<APP_DIR>/runtime/``.
    """
    packaged = APP_DIR.parent / "resources" / "runtime"
    if packaged.is_dir():
        return packaged
    return APP_DIR / "runtime"


# ---------------------------------------------------------------------------
# Individual tool paths
# ---------------------------------------------------------------------------

def bundled_python() -> Optional[str]:
    """Path to the bundled Python executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [root / "python" / "python.exe", root / "python.exe"]
    else:
        candidates = [root / "python" / "bin" / "python3", root / "python"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_git() -> Optional[str]:
    """Path to the bundled Git executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "git" / "cmd" / "git.exe",
            root / "git" / "bin" / "git.exe",
        ]
    else:
        candidates = [root / "git" / "bin" / "git", root / "git"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_bash() -> Optional[str]:
    """Path to the bundled Bash executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "git" / "bin" / "bash.exe",
            root / "git" / "usr" / "bin" / "bash.exe",
            root / "bash" / "bash.exe",
        ]
    else:
        candidates = [root / "bash" / "bash", "/bin/bash"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_svn() -> Optional[str]:
    """Path to the bundled SVN executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "svn" / "svn.exe",
            root / "svn" / "bin" / "svn.exe",
        ]
    else:
        candidates = [root / "svn" / "bin" / "svn", root / "svn"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_node() -> Optional[str]:
    """Path to the bundled Node.js executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "node" / "node.exe",
            root / "node" / "bin" / "node.exe",
        ]
    else:
        candidates = [root / "node" / "bin" / "node", root / "node"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_npm() -> Optional[str]:
    """Path to the bundled npm executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "node" / "npm.cmd",
            root / "node" / "npm",
            root / "node" / "bin" / "npm.cmd",
        ]
    else:
        candidates = [root / "node" / "bin" / "npm", root / "npm"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_npx() -> Optional[str]:
    """Path to the bundled npx executable, or None."""
    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "node" / "npx.cmd",
            root / "node" / "npx",
            root / "node" / "bin" / "npx.cmd",
        ]
    else:
        candidates = [root / "node" / "bin" / "npx", root / "npx"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


# ---------------------------------------------------------------------------
# Node shim directory
# ---------------------------------------------------------------------------

def node_shim_dir() -> Path:
    """Return (and create) a directory containing node/npm/npx shims.

    On Windows these are ``.cmd`` wrappers; on Unix they are shell scripts.
    The directory should be prepended to PATH so that child processes
    pick up the bundled Node.
    """
    shim_dir = APP_DIR / "tmp" / "node-shims"
    shim_dir.mkdir(parents=True, exist_ok=True)

    node = bundled_node()
    npm = bundled_npm()
    npx = bundled_npx()

    if os.name == "nt":
        # Create .cmd shims
        if node:
            (shim_dir / "node.cmd").write_text(
                f'@echo off\r\n"{node}" %*\r\n', encoding="utf-8"
            )
        if npm:
            (shim_dir / "npm.cmd").write_text(
                f'@echo off\r\n"{npm}" %*\r\n', encoding="utf-8"
            )
        if npx:
            (shim_dir / "npx.cmd").write_text(
                f'@echo off\r\n"{npx}" %*\r\n', encoding="utf-8"
            )
    else:
        # Create shell shims
        if node:
            shim = shim_dir / "node"
            shim.write_text(f'#!/bin/sh\nexec "{node}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)
        if npm:
            shim = shim_dir / "npm"
            shim.write_text(f'#!/bin/sh\nexec "{npm}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)
        if npx:
            shim = shim_dir / "npx"
            shim.write_text(f'#!/bin/sh\nexec "{npx}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)

    return shim_dir


def ensure_node_command_shims() -> str:
    """Ensure node shims exist and return the shim directory path."""
    return str(node_shim_dir())


# ---------------------------------------------------------------------------
# Existing bundled tool lookup
# ---------------------------------------------------------------------------

def existing_bundled_tool(name: str) -> Optional[str]:
    """Return the path to a bundled tool by name, or None.

    Supported names: python, git, bash, svn, node, npm, npx.
    """
    dispatch = {
        "python": bundled_python,
        "git": bundled_git,
        "bash": bundled_bash,
        "svn": bundled_svn,
        "node": bundled_node,
        "npm": bundled_npm,
        "npx": bundled_npx,
    }
    fn = dispatch.get(name)
    if fn is None:
        return None
    return fn()


# ---------------------------------------------------------------------------
# PATH helpers
# ---------------------------------------------------------------------------

def path_with_bundled_node(existing_path: Optional[str] = None) -> str:
    """Return a PATH string with the bundled Node directory prepended."""
    node = bundled_node()
    if not node:
        return existing_path or os.environ.get("PATH", "")
    node_dir = str(Path(node).parent)
    base = existing_path or os.environ.get("PATH", "")
    return f"{node_dir}{os.pathsep}{base}"


# ---------------------------------------------------------------------------
# Package manager resolution
# ---------------------------------------------------------------------------

def package_manager_executable(project_dir: Path) -> str:
    """Determine the package manager executable for a project.

    Checks for pnpm-lock.yaml, yarn.lock, then defaults to npm.
    """
    if (project_dir / "pnpm-lock.yaml").is_file():
        pnpm = bundled_npm()  # fallback
        for name in ("pnpm", "pnpm.cmd"):
            found = shutil.which(name)
            if found:
                return found
        # Check bundled
        root = runtime_root()
        if os.name == "nt":
            candidate = root / "node" / "pnpm.cmd"
        else:
            candidate = root / "node" / "bin" / "pnpm"
        if candidate.is_file():
            return str(candidate)
        return "pnpm"

    if (project_dir / "yarn.lock").is_file():
        return "yarn"

    npm = bundled_npm()
    return npm or "npm"


# ---------------------------------------------------------------------------
# Node version checks
# ---------------------------------------------------------------------------

def bundled_node_version() -> Optional[str]:
    """Return the version string of the bundled Node, or None."""
    node = bundled_node()
    if not node:
        return None
    try:
        r = run_process([node, "--version"])
        return r.stdout.strip().lstrip("v")
    except Exception:
        return None


def bundled_node_major_version() -> Optional[int]:
    """Return the major version number of the bundled Node, or None."""
    ver = bundled_node_version()
    if not ver:
        return None
    match = re.match(r"(\d+)", ver)
    return int(match.group(1)) if match else None


def ensure_required_node_version() -> bool:
    """Check that the bundled (or system) Node meets the required version.

    Returns True if the requirement is satisfied, False otherwise.
    """
    ver = bundled_node_version()
    if not ver:
        # Try system node
        try:
            r = run_process(["node", "--version"])
            ver = r.stdout.strip().lstrip("v")
        except Exception:
            return False

    required_parts = [int(x) for x in REQUIRED_NODE_VERSION.split(".")]
    actual_parts = [int(x) for x in ver.split(".")[:3]]

    return actual_parts >= required_parts


# Need shutil for package_manager_executable
import shutil

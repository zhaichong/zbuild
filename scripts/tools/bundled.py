# -*- coding: utf-8 -*-
"""Bundled tool path resolution.

Provides paths to bundled runtimes (Python, Git, Bash, SVN, Node, npm)
that ship alongside the Electron application, and helpers to set up
shims so that child processes pick up the bundled versions.
"""

import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional

from core.constants import APP_DIR
from tools.exec import run_process

logger = logging.getLogger(__name__)

REQUIRED_NODE_VERSION = "14.21.3"

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------

def _runtime_config_path() -> Path:
    """Path to runtime-config.json alongside the per-user runtime root."""
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        return Path(local_appdata) / "zbuild" / "runtime-config.json"
    return Path.home() / "zbuild-runtime-config.json"


def _read_config() -> dict:
    """Read runtime-config.json, returning an empty dict on failure."""
    try:
        return json.loads(_runtime_config_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_override(kind: str) -> Optional[str]:
    """Return the user-configured system-runtime override path, or None.

    The path is only returned if the file actually exists on disk.
    """
    cfg = _read_config()
    key = "overridePython" if kind == "python" else "overrideNode"
    val = cfg.get(key)
    if isinstance(val, str) and val:
        p = Path(val)
        if p.is_file():
            return str(p)
    return None


def _runtime_roots() -> list:
    """Ordered runtime roots (matches electron/runtime.js).

    1. Dev repository (APP_DIR / "runtime") when present as a directory.
    2. Per-user runtime root (ZBUILD_RUNTIME_ROOT or %LOCALAPPDATA%\\zbuild\\runtime).

    Legacy resources/runtime is intentionally omitted so old bundled installs
    cannot bypass online-setup manifest version / hash checks.
    """
    roots = []
    dev = APP_DIR / "runtime"
    if dev.is_dir():
        roots.append(dev)
    runtime_root_env = os.environ.get("ZBUILD_RUNTIME_ROOT", "")
    if runtime_root_env:
        user = Path(runtime_root_env)
        if user.is_dir() and user not in roots:
            roots.append(user)
    else:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            user = Path(local_appdata) / "zbuild" / "runtime"
            if user.is_dir() and user not in roots:
                roots.append(user)
    return roots


def runtime_root() -> Path:
    """Return the preferred root directory for bundled runtimes (git/bash/svn).

    Prefer the first existing root. For python/node, use bundled_python /
    find_node14_dir which select per-executable so an incomplete root does not
    shadow a complete one.
    """
    roots = _runtime_roots()
    if roots:
        return roots[0]
    return APP_DIR / "runtime"


# ---------------------------------------------------------------------------
# Individual tool paths
# ---------------------------------------------------------------------------

def bundled_python() -> Optional[str]:
    """Path to the bundled Python executable, or None.

    Candidate order (per executable, not per root-directory existence):
    override → each runtime root's python.exe. Incomplete dev trees do not
    shadow a complete user install.
    """
    override = _read_override("python")
    if override:
        return override
    for root in _runtime_roots():
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


def find_node14_dir() -> Optional[Path]:
    """Find the directory containing a Node.js 14 installation.

    Scans each runtime root for node.exe (same order as electron/runtime.js).
    System Node (Volta/NVM/PATH) is intentionally not used as a fallback.
    """
    for root in _runtime_roots():
        cand = root / "node"
        if (cand / "node.exe").is_file() or (cand / "bin" / "node").is_file() or (cand / "node").is_file():
            return cand
    return None


def bundled_node() -> Optional[str]:
    """Path to the Node.js 14 executable, or None."""
    override = _read_override("node")
    if override:
        return override
    node14_dir = find_node14_dir()
    if node14_dir:
        if os.name == "nt":
            for c in [node14_dir / "node.exe", node14_dir / "bin" / "node.exe"]:
                if c.is_file():
                    return str(c)
        else:
            for c in [node14_dir / "bin" / "node", node14_dir / "node"]:
                if c.is_file():
                    return str(c)

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


def _node14_cli_js(tool: str) -> Optional[str]:
    """Return path to Node 14's bundled ``npm-cli.js`` / ``npx-cli.js``, or None.

    Prefer invoking these via ``node <cli.js>`` rather than the stock
    ``npm.cmd`` / ``npm`` wrappers.  Those wrappers re-resolve the global
    ``prefix`` and will silently switch to a newer npm (e.g. Volta Node 22's
    npm 10) when one is installed globally — which then crashes on Node 14
    (``SyntaxError: Unexpected token &&=``).
    """
    node14_dir = find_node14_dir()
    if not node14_dir:
        return None
    name = "npm-cli.js" if tool == "npm" else "npx-cli.js"
    cand = node14_dir / "node_modules" / "npm" / "bin" / name
    return str(cand) if cand.is_file() else None


def _stock_npm_path() -> Optional[str]:
    """Path to the stock npm launcher next to Node 14 (may global-prefix redirect)."""
    node14_dir = find_node14_dir()
    if node14_dir:
        if os.name == "nt":
            for c in [node14_dir / "npm.cmd", node14_dir / "npm", node14_dir / "bin" / "npm.cmd"]:
                if c.is_file():
                    return str(c)
        else:
            for c in [node14_dir / "bin" / "npm", node14_dir / "npm"]:
                if c.is_file():
                    return str(c)

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


def _stock_npx_path() -> Optional[str]:
    """Path to the stock npx launcher next to Node 14 (may global-prefix redirect)."""
    node14_dir = find_node14_dir()
    if node14_dir:
        if os.name == "nt":
            for c in [node14_dir / "npx.cmd", node14_dir / "npx", node14_dir / "bin" / "npx.cmd"]:
                if c.is_file():
                    return str(c)
        else:
            for c in [node14_dir / "bin" / "npx", node14_dir / "npx"]:
                if c.is_file():
                    return str(c)

    root = runtime_root()
    if os.name == "nt":
        candidates = [
            root / "node" / "npx.cmd",
            root / "node" / "npx",
            root / "node" / "bin" / "npx.cmd",
        ]
    else:
        candidates = [root / "node" / "bin" / "npx", root / "node"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def bundled_npm() -> Optional[str]:
    """Path to a safe npm entrypoint for Node 14 (shim preferred), or None.

    Returns the generated shim path so callers never hit stock ``npm.cmd``'s
    global-prefix redirect onto a foreign (newer) npm.
    """
    if not bundled_node() and not _stock_npm_path():
        return None
    shim = node_shim_dir()
    if os.name == "nt":
        cand = shim / "npm.cmd"
    else:
        cand = shim / "npm"
    return str(cand) if cand.is_file() else _stock_npm_path()


def bundled_npx() -> Optional[str]:
    """Path to a safe npx entrypoint for Node 14 (shim preferred), or None."""
    if not bundled_node() and not _stock_npx_path():
        return None
    shim = node_shim_dir()
    if os.name == "nt":
        cand = shim / "npx.cmd"
    else:
        cand = shim / "npx"
    return str(cand) if cand.is_file() else _stock_npx_path()


# ---------------------------------------------------------------------------
# Node shim directory
# ---------------------------------------------------------------------------

def npm_isolated_prefix_dir() -> Path:
    """Directory used as npm global prefix during builds.

    Kept empty of a foreign ``node_modules/npm`` so stock npm launchers cannot
    re-route onto Volta/system npm 10+ while Node 14 is the runtime.
    """
    prefix = APP_DIR / "tmp" / "npm-global-prefix"
    prefix.mkdir(parents=True, exist_ok=True)
    return prefix


def node_shim_dir() -> Path:
    """Return (and create) a directory containing node/npm/npx shims for Node 14.

    Creates both .cmd wrappers (for Windows cmd/powershell) and POSIX shell scripts
    (for Git Bash / MSYS2 / Unix shell) so that whenever deploy.sh or npm is run,
    Node 14 and npm 6 are unconditionally used.

    CRITICAL: shims must invoke ``node <npm-cli.js>`` directly.  Stock
    ``npm.cmd`` / ``npm`` scripts call ``npm prefix -g`` and, when a newer npm
    is installed in the global prefix (common with Volta Node 18+/22), re-exec
    that foreign CLI under Node 14 — which fails with
    ``npm v10 is known not to run on Node.js v14`` / ``Unexpected token &&=``.
    """
    shim_dir = APP_DIR / "tmp" / "node-shims"
    shim_dir.mkdir(parents=True, exist_ok=True)

    node = bundled_node()
    npm_cli = _node14_cli_js("npm")
    npx_cli = _node14_cli_js("npx")
    stock_npm = _stock_npm_path()
    stock_npx = _stock_npx_path()

    if node:
        # Create .cmd shims (Windows CMD / PowerShell).
        # Write in binary mode with explicit \r\n to avoid Python text-mode
        # double-converting \r\n into \r\r\n on Windows.
        (shim_dir / "node.cmd").write_bytes(
            f'@echo off\r\n"{node}" %*\r\n'.encode("utf-8")
        )
        # Prefer node+cli.js over stock npm.cmd (avoids global-prefix hijack).
        if npm_cli:
            (shim_dir / "npm.cmd").write_bytes(
                f'@echo off\r\n"{node}" "{npm_cli}" %*\r\n'.encode("utf-8")
            )
        elif stock_npm:
            (shim_dir / "npm.cmd").write_bytes(
                f'@echo off\r\n"{stock_npm}" %*\r\n'.encode("utf-8")
            )
        if npx_cli:
            (shim_dir / "npx.cmd").write_bytes(
                f'@echo off\r\n"{node}" "{npx_cli}" %*\r\n'.encode("utf-8")
            )
        elif stock_npx:
            (shim_dir / "npx.cmd").write_bytes(
                f'@echo off\r\n"{stock_npx}" %*\r\n'.encode("utf-8")
            )

        # Create shell shims (Git Bash on Windows and POSIX systems).
        # CRITICAL: use newline='\n' so Python does NOT convert \n -> \r\n on
        # Windows.  A CRLF shebang (#!/bin/sh\r) is unrecognised by bash and
        # causes it to silently skip the shim, falling back to Volta's npm.
        node_posix = str(node).replace("\\", "/")
        shim_node = shim_dir / "node"
        shim_node.write_text(
            f'#!/bin/sh\nexec "{node_posix}" "$@"\n',
            encoding="utf-8", newline="\n"
        )
        try:
            shim_node.chmod(0o755)
        except Exception:
            pass

        shim_npm = shim_dir / "npm"
        if npm_cli:
            npm_cli_posix = npm_cli.replace("\\", "/")
            shim_npm.write_text(
                f'#!/bin/sh\nexec "{node_posix}" "{npm_cli_posix}" "$@"\n',
                encoding="utf-8", newline="\n"
            )
        elif stock_npm:
            npm_posix = str(stock_npm).replace("\\", "/")
            shim_npm.write_text(
                f'#!/bin/sh\nexec "{npm_posix}" "$@"\n',
                encoding="utf-8", newline="\n"
            )
        try:
            shim_npm.chmod(0o755)
        except Exception:
            pass

        shim_npx = shim_dir / "npx"
        if npx_cli:
            npx_cli_posix = npx_cli.replace("\\", "/")
            shim_npx.write_text(
                f'#!/bin/sh\nexec "{node_posix}" "{npx_cli_posix}" "$@"\n',
                encoding="utf-8", newline="\n"
            )
        elif stock_npx:
            npx_posix = str(stock_npx).replace("\\", "/")
            shim_npx.write_text(
                f'#!/bin/sh\nexec "{npx_posix}" "$@"\n',
                encoding="utf-8", newline="\n"
            )
        try:
            shim_npx.chmod(0o755)
        except Exception:
            pass

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
    """Check that the bundled Node meets the required version.

    Returns True if the requirement is satisfied, False otherwise.
    System Node is not consulted as a fallback.
    """
    ver = bundled_node_version()
    if not ver:
        return False

    required_parts = [int(x) for x in REQUIRED_NODE_VERSION.split(".")]
    actual_parts = [int(x) for x in ver.split(".")[:3]]

    return actual_parts >= required_parts

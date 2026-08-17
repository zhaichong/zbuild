# -*- coding: utf-8 -*-
"""Dependency management: install project dependencies (npm/pnpm/yarn)."""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from core.errors import DependencyError
from tools.exec import run_process, run_process_stream
from tools.bundled import (
    bundled_node,
    bundled_npm,
    bundled_npx,
    node_shim_dir,
    package_manager_executable,
)

logger = logging.getLogger(__name__)


FINGERPRINT_FILE = ".zbuild_deps_fingerprint"


def dependency_fingerprint(project_path: Union[Path, str]) -> str:
    """Compute a fingerprint of the dependency specification.

    Combines hashes of package.json, package-lock.json (or equivalent),
    and any .npmrc to detect when dependencies need reinstalling.
    """
    project = Path(project_path)
    parts: List[str] = []

    for name in ("package.json", "package-lock.json", "pnpm-lock.yaml",
                 "yarn.lock", ".npmrc"):
        f = project / name
        if f.is_file():
            h = hashlib.sha256()
            h.update(f.read_bytes())
            parts.append(f"{name}:{h.hexdigest()[:16]}")

    return "|".join(parts) if parts else ""


def dependency_install_command(project_path: Union[Path, str]) -> List[str]:
    """Return the command to install dependencies for the project."""
    project = Path(project_path)
    pm = package_manager_executable(project)

    if "pnpm" in pm:
        return [pm, "install", "--frozen-lockfile"]
    elif "yarn" in pm:
        return [pm, "install", "--frozen-lockfile"]
    else:
        return [pm, "install"]


def _node_env() -> Dict[str, str]:
    """Build environment variables guaranteeing Node.js 14 on PATH.

    Also isolates npm's global prefix so stock ``npm.cmd`` / ``npm`` wrappers
    cannot re-route onto a foreign newer npm (e.g. Volta Node 22 / npm 10)
    when one is present under the user global prefix.
    """
    from tools.bundled import find_node14_dir, node_shim_dir, npm_isolated_prefix_dir

    env = os.environ.copy()

    # 1. Node shims directory (node, npm, npx wrappers → node + local npm-cli.js)
    shim_dir = node_shim_dir()

    # 2. Node 14 binary directory
    node14_dir = find_node14_dir()

    paths_to_prepend: List[str] = [str(shim_dir)]
    if node14_dir:
        paths_to_prepend.append(str(node14_dir))

    # Prepend shims and Node 14 directory to PATH and Path
    current_path = env.get("PATH", "") or env.get("Path", "")
    new_path = os.pathsep.join(paths_to_prepend + [current_path])
    env["PATH"] = new_path
    env["Path"] = new_path

    # Point npm and node helpers directly to Node 14
    node_exe = bundled_node()
    if node_exe:
        env["npm_node_execpath"] = node_exe
        env["NODE_EXE"] = node_exe

    # Isolate global prefix so stock npm launchers do not pick up npm 10+ from
    # %AppData%\npm or a Volta Node 18+/22 image (which crash under Node 14).
    prefix = str(npm_isolated_prefix_dir())
    env["npm_config_prefix"] = prefix
    # Clear any user/project override that would reintroduce a foreign npm.
    env.pop("NPM_CONFIG_PREFIX", None)
    env["NPM_CONFIG_PREFIX"] = prefix

    # Strip --openssl-legacy-provider from NODE_OPTIONS.
    # This flag is only valid for Node >= 17 (OpenSSL 3) and causes Node 14 to
    # abort immediately with "not allowed in NODE_OPTIONS".
    _raw_opts = env.get("NODE_OPTIONS", "")
    _cleaned = " ".join(f for f in _raw_opts.split() if f != "--openssl-legacy-provider")
    env["NODE_OPTIONS"] = _cleaned

    return env


def ensure_dependencies(
    project_path: Union[Path, str],
    *,
    force: bool = False,
    on_line: Optional[callable] = None,
) -> bool:
    """Install project dependencies if needed.

    Parameters
    ----------
    project_path:
        Path to the project directory.
    force:
        If True, always reinstall even if node_modules exists and fingerprint matches.
    on_line:
        Optional callback for streaming output.

    Returns
    -------
    bool:
        True if dependencies are satisfied.

    Raises
    ------
    DependencyError
        If the install command fails.
    """
    project = Path(project_path)
    node_modules = project / "node_modules"
    current_fp = dependency_fingerprint(project)
    fp_file = node_modules / FINGERPRINT_FILE

    if not force and node_modules.is_dir() and current_fp:
        if fp_file.is_file():
            try:
                cached_fp = fp_file.read_text(encoding="utf-8").strip()
                if cached_fp == current_fp:
                    logger.info("Dependencies are up to date (fingerprint match), skipping install for %s", project)
                    return True
            except Exception as exc:
                logger.warning("Failed to read dependency fingerprint for %s: %s", project, exc)

    cmd = dependency_install_command(project)
    env = _node_env()

    logger.info("Installing dependencies: %s (in %s)", cmd, project)

    try:
        result = run_process_stream(
            cmd,
            cwd=project,
            env=env,
            on_line=on_line,
            timeout=300,  # 5 minute timeout
        )
        if result.returncode != 0:
            raise DependencyError(
                f"Dependency install failed (exit {result.returncode}): "
                f"{result.stdout[-500:] if result.stdout else ''}"
            )

        if current_fp and node_modules.is_dir():
            try:
                fp_file.write_text(current_fp, encoding="utf-8")
            except Exception as exc:
                logger.warning("Failed to write dependency fingerprint for %s: %s", project, exc)

        return True
    except DependencyError:
        raise
    except Exception as exc:
        raise DependencyError(f"Dependency install error: {exc}") from exc

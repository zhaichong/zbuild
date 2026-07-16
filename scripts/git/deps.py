# -*- coding: utf-8 -*-
"""Dependency management: install project dependencies (npm/pnpm/yarn)."""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

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


def dependency_fingerprint(project_path: Path | str) -> str:
    """Compute a fingerprint of the dependency specification.

    Combines hashes of package.json, package-lock.json (or equivalent),
    and any .npmrc to detect when dependencies need reinstalling.
    """
    project = Path(project_path)
    parts: list[str] = []

    for name in ("package.json", "package-lock.json", "pnpm-lock.yaml",
                 "yarn.lock", ".npmrc"):
        f = project / name
        if f.is_file():
            h = hashlib.sha256()
            h.update(f.read_bytes())
            parts.append(f"{name}:{h.hexdigest()[:16]}")

    return "|".join(parts) if parts else ""


def dependency_install_command(project_path: Path | str) -> list[str]:
    """Return the command to install dependencies for the project."""
    project = Path(project_path)
    pm = package_manager_executable(project)

    if "pnpm" in pm:
        return [pm, "install", "--frozen-lockfile"]
    elif "yarn" in pm:
        return [pm, "install", "--frozen-lockfile"]
    else:
        return [pm, "ci"]


def _node_env() -> dict[str, str]:
    """Build environment variables with bundled Node on PATH."""
    env: dict[str, str] = {}
    node = bundled_node()
    if node:
        node_dir = str(Path(node).parent)
        env["PATH"] = f"{node_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    return env


def ensure_dependencies(
    project_path: Path | str,
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
        If True, always reinstall even if node_modules exists.
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

    if not force and node_modules.is_dir():
        logger.debug("node_modules exists, skipping install for %s", project)
        return True

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
        return True
    except DependencyError:
        raise
    except Exception as exc:
        raise DependencyError(f"Dependency install error: {exc}") from exc

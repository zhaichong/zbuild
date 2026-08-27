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
INSTALL_LOCK_FILE = ".zbuild_installing.lock"


def dependency_fingerprint(project_path: Union[Path, str]) -> str:
    """Compute a fingerprint of the dependency specification.

    Combines hashes of package.json, package-lock.json, pnpm-lock.yaml,
    yarn.lock, and any .npmrc to detect when dependencies need reinstalling.
    """
    project = Path(project_path)
    parts: List[str] = []

    for name in (
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        ".npmrc",
    ):
        f = project / name
        if f.is_file():
            h = hashlib.sha256()
            h.update(f.read_bytes())
            parts.append(f"{name}:{h.hexdigest()[:16]}")

    return "|".join(parts) if parts else ""


def compute_deps_slot_key(project_path: Union[Path, str]) -> str:
    """Compute a deterministic short slot key for dependency isolation cache.

    Returns a 16-character hex hash representing the exact dependency manifest
    state, or 'default' if no dependency manifests exist.
    """
    fp = dependency_fingerprint(project_path)
    if not fp:
        return "default"
    return hashlib.sha256(fp.encode("utf-8")).hexdigest()[:16]


def dependency_install_command(project_path: Union[Path, str]) -> List[str]:
    """Return the command to install dependencies for the project."""
    project = Path(project_path)
    pm = package_manager_executable(project)
    # Prefer offline cache for npm/pnpm/yarn to avoid redownloading known tarballs
    if pm == "npm" or pm.endswith("npm") or pm.endswith("npm.cmd"):
        return [pm, "install", "--prefer-offline", "--no-audit", "--no-fund", "--progress=false"]
    if pm == "pnpm" or pm.endswith("pnpm") or pm.endswith("pnpm.cmd"):
        return [pm, "install", "--prefer-offline"]
    if pm == "yarn" or pm.endswith("yarn") or pm.endswith("yarn.cmd"):
        return [pm, "install", "--prefer-offline"]
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

    # Unified local npm cache directory across all isolated workspaces
    from core.constants import DATA_DIR
    npm_cache_dir = DATA_DIR / "npm_cache"
    npm_cache_dir.mkdir(parents=True, exist_ok=True)
    env["npm_config_cache"] = str(npm_cache_dir)
    env["NPM_CONFIG_CACHE"] = str(npm_cache_dir)

    # Strip --openssl-legacy-provider from NODE_OPTIONS.
    # This flag is only valid for Node >= 17 (OpenSSL 3) and causes Node 14 to
    # abort immediately with "not allowed in NODE_OPTIONS".
    _raw_opts = env.get("NODE_OPTIONS", "")
    _opts_parts = [f for f in _raw_opts.split() if f != "--openssl-legacy-provider"]
    if not any(opt.startswith("--max-old-space-size") for opt in _opts_parts):
        _opts_parts.append("--max-old-space-size=8192")
    env["NODE_OPTIONS"] = " ".join(_opts_parts).strip()

    # Full-power performance flags: expand threadpool & disable unnecessary CLI overheads
    env["UV_THREADPOOL_SIZE"] = "16"
    env["CI"] = "true"
    env["JOBS"] = "max"
    env["npm_config_progress"] = "false"
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"
    env["npm_config_update_notifier"] = "false"

    # Mirror speeds up binary and dependency downloads for Vue CLI, node-sass, image-min plugins
    env["npm_config_registry"] = "https://registry.npmmirror.com"
    env["NPM_CONFIG_REGISTRY"] = "https://registry.npmmirror.com"
    env["SASS_BINARY_SITE"] = "https://npmmirror.com/mirrors/node-sass"
    env["OPTIPNG_BIN_DOWNLOAD_BASE_URL"] = "https://npmmirror.com/mirrors/optipng-bin"
    env["PNGQUANT_BIN_DOWNLOAD_BASE_URL"] = "https://npmmirror.com/mirrors/pngquant-bin"
    env["GIFSICLE_BIN_DOWNLOAD_BASE_URL"] = "https://npmmirror.com/mirrors/gifsicle"
    env["CWEBP_BIN_DOWNLOAD_BASE_URL"] = "https://npmmirror.com/mirrors/cwebp-bin"
    env["ELECTRON_MIRROR"] = "https://npmmirror.com/mirrors/electron/"

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
                    if on_line:
                        on_line("⚡ 依赖未发生变动 (指纹匹配)，跳过依赖安装")
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

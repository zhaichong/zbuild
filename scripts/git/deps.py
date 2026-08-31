# -*- coding: utf-8 -*-
"""Dependency management: install project dependencies (npm/pnpm/yarn)."""

import hashlib
import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

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


def dependency_install_command(project_path: Union[Path, str], version: str = "14") -> List[str]:
    """Return the command to install dependencies for the project."""
    project = Path(project_path)
    pm = package_manager_executable(project)
    # Prefer offline cache for npm/pnpm/yarn to avoid redownloading known tarballs
    if pm == "npm" or pm.endswith("npm") or pm.endswith("npm.cmd"):
        cmd = [pm, "install", "--prefer-offline", "--no-audit", "--no-fund", "--progress=false"]
        if str(version).startswith("14"):
            cmd.extend(["--no-optional", "--ignore-engines"])
        return cmd
    if pm == "pnpm" or pm.endswith("pnpm") or pm.endswith("pnpm.cmd"):
        return [pm, "install", "--prefer-offline"]
    if pm == "yarn" or pm.endswith("yarn") or pm.endswith("yarn.cmd"):
        cmd = [pm, "install", "--prefer-offline"]
        if str(version).startswith("14"):
            cmd.append("--ignore-engines")
        return cmd
    return [pm, "install"]


def _node_env(version: str = "14") -> Dict[str, str]:
    """Build environment variables guaranteeing the required Node version on PATH.

    Also isolates npm's global prefix so stock ``npm.cmd`` / ``npm`` wrappers
    cannot re-route onto a foreign newer npm (e.g. Volta Node 22 / npm 10)
    when one is present under the user global prefix.
    """
    from tools.bundled import (
        find_node14_dir,
        find_node22_dir,
        bundled_node,
        node_shim_dir,
        npm_isolated_prefix_dir,
    )

    env = os.environ.copy()

    if str(version).startswith("22"):
        node22_dir = find_node22_dir()
        paths_to_prepend: List[str] = []
        if node22_dir:
            paths_to_prepend.append(str(node22_dir))
            if os.name == "nt" and (node22_dir / "bin").is_dir():
                paths_to_prepend.append(str(node22_dir / "bin"))

        # Clean out any Node 14 shims or Node 14 directory to avoid PATH pollution
        shim_dir_str = str(node_shim_dir())
        node14_dir = find_node14_dir()
        node14_dir_str = str(node14_dir) if node14_dir else ""
        current_path = env.get("PATH", "") or env.get("Path", "")
        cleaned_parts = [
            p for p in current_path.split(os.pathsep)
            if p and p != shim_dir_str and (not node14_dir_str or p != node14_dir_str)
        ]
        new_path = os.pathsep.join(paths_to_prepend + cleaned_parts)
        env["PATH"] = new_path
        env["Path"] = new_path

        # Unset Node 14 isolated prefix so Node 22 / npm 10 uses its native global prefix
        env.pop("npm_config_prefix", None)
        env.pop("NPM_CONFIG_PREFIX", None)

        node_exe = bundled_node("22")
        if node_exe:
            env["npm_node_execpath"] = node_exe
            env["NODE_EXE"] = node_exe
            env["NODE22_EXE"] = node_exe
        if node22_dir:
            env["NODE22_DIR"] = str(node22_dir)

        # Expose Node 14 paths as env vars for scripts that need explicit cross-invocations
        node14_exe = bundled_node("14")
        if node14_exe:
            env["NODE14_EXE"] = node14_exe
        if node14_dir:
            env["NODE14_DIR"] = str(node14_dir)

        from core.constants import DATA_DIR
        npm_cache_dir = DATA_DIR / "npm_cache"
        npm_cache_dir.mkdir(parents=True, exist_ok=True)
        env["npm_config_cache"] = str(npm_cache_dir)
        env["NPM_CONFIG_CACHE"] = str(npm_cache_dir)

        env["UV_THREADPOOL_SIZE"] = "16"
        env["CI"] = "true"
        env["JOBS"] = "max"
        env["npm_config_progress"] = "false"
        env["npm_config_audit"] = "false"
        env["npm_config_fund"] = "false"
        env["npm_config_update_notifier"] = "false"
        env["npm_config_registry"] = "https://registry.npmmirror.com"
        env["NPM_CONFIG_REGISTRY"] = "https://registry.npmmirror.com"
        return env

    # Default: Node 14
    shim_dir = node_shim_dir()
    node14_dir = find_node14_dir()

    paths_to_prepend = [str(shim_dir)]
    if node14_dir:
        paths_to_prepend.append(str(node14_dir))

    # Prepend shims and Node 14 directory to PATH and Path
    current_path = env.get("PATH", "") or env.get("Path", "")
    new_path = os.pathsep.join(paths_to_prepend + [current_path])
    env["PATH"] = new_path
    env["Path"] = new_path

    # Point npm and node helpers directly to Node 14
    node_exe = bundled_node("14")
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
    env["npm_config_engine_strict"] = "false"
    env["npm_config_optional"] = "false"

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


# ---------------------------------------------------------------------------
# npmmirror auto-sync on ETARGET / missing version
# ---------------------------------------------------------------------------

NPMMIRROR_REGISTRY = "https://registry.npmmirror.com"


def parse_package_spec(spec: str) -> Tuple[str, str]:
    """Parse a package spec like ``@vue/compiler-core@3.5.42`` into (name, version)."""
    spec = spec.strip().rstrip(".:,;")
    if spec.startswith("@"):
        parts = spec[1:].split("@", 1)
        pkg_name = "@" + parts[0]
        version = parts[1] if len(parts) > 1 else ""
    else:
        parts = spec.split("@", 1)
        pkg_name = parts[0]
        version = parts[1] if len(parts) > 1 else ""
    return pkg_name, version


def extract_missing_packages_from_output(output: str) -> List[Tuple[str, str]]:
    """Extract missing packages and versions from npm/pnpm/yarn error output."""
    results: List[Tuple[str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    # Pattern 1: npm "No matching version found for <spec>"
    for match in re.findall(r"No matching version found for\s+([^\s\r\n]+)", output):
        pkg, ver = parse_package_spec(match)
        if pkg and (pkg, ver) not in seen:
            seen.add((pkg, ver))
            results.append((pkg, ver))

    # Pattern 2: npm "notarget No matching version found for <spec>"
    for match in re.findall(r"notarget\s+([^\s\r\n]+)", output):
        if "@" in match:
            pkg, ver = parse_package_spec(match)
            if pkg and (pkg, ver) not in seen:
                seen.add((pkg, ver))
                results.append((pkg, ver))

    return results


def trigger_npmmirror_sync(package_name: str) -> bool:
    """Request npmmirror to sync a package from the official npm registry.

    PUT https://registry.npmmirror.com/-/package/<encoded_name>/syncs
    """
    try:
        encoded_name = urllib.parse.quote(package_name, safe="")
        url = f"{NPMMIRROR_REGISTRY}/-/package/{encoded_name}/syncs"
        req = urllib.request.Request(url, method="PUT", headers={"User-Agent": "zbuild/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201, 202)
    except Exception as exc:
        logger.debug("Failed to trigger npmmirror sync for %s: %s", package_name, exc)
        return False


def wait_for_npmmirror_sync(
    package_name: str,
    target_version: str = "",
    *,
    timeout_seconds: float = 45.0,
    poll_interval: float = 3.0,
) -> bool:
    """Poll npmmirror until the target package (or specific version) is available."""
    encoded_name = urllib.parse.quote(package_name, safe="")
    if target_version and not re.search(r"[\^~><*=]", target_version):
        encoded_ver = urllib.parse.quote(target_version, safe="")
        url = f"{NPMMIRROR_REGISTRY}/{encoded_name}/{encoded_ver}"
    else:
        url = f"{NPMMIRROR_REGISTRY}/{encoded_name}"

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "zbuild/2.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(poll_interval)
    return False


def attempt_npmmirror_auto_sync(
    output: str,
    *,
    on_line: Optional[callable] = None,
) -> bool:
    """Detect ETARGET errors in output, trigger npmmirror sync, and wait for completion.

    Returns True if at least one missing package was synced and ready for retry.
    """
    if "ETARGET" not in output and "No matching version found" not in output and "notarget" not in output:
        return False

    missing = extract_missing_packages_from_output(output)
    if not missing:
        return False

    synced_any = False
    for pkg_name, ver in missing:
        spec_str = f"{pkg_name}@{ver}" if ver else pkg_name
        msg = f"🔄 检测到镜像源缺失依赖版本 {spec_str} (ETARGET)，正在自动触发 npmmirror 同步..."
        logger.info(msg)
        if on_line:
            on_line(msg)

        if trigger_npmmirror_sync(pkg_name):
            if on_line:
                on_line(f"⏳ npmmirror 同步已触发，等待镜像更新 (最多 45s)...")
            if wait_for_npmmirror_sync(pkg_name, ver, timeout_seconds=45.0):
                success_msg = f"✅ 依赖 {spec_str} 已在 npmmirror 镜像同步成功，准备自动重试安装"
                logger.info(success_msg)
                if on_line:
                    on_line(success_msg)
                synced_any = True
            else:
                if on_line:
                    on_line(f"⚠️ npmmirror 同步超时，将尝试直接重试")
        else:
            if on_line:
                on_line(f"⚠️ 无法请求 npmmirror 同步接口，将尝试直接重试")

    return synced_any or len(missing) > 0


def ensure_dependencies(
    project_path: Union[Path, str],
    *,
    force: bool = False,
    on_line: Optional[callable] = None,
    build_command: str = "deploy.sh",
    branch: str = "",
    parent_command: str = "",
    parent_branch: str = "",
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
    build_command:
        Project build command (used for Node version resolution).
    branch:
        Target branch (used for Node version resolution).
    parent_command:
        Parent build command if part of composite task.
    parent_branch:
        Parent branch if part of composite task.

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

    from git.build_cmd import resolve_project_node_version
    node_ver = resolve_project_node_version(
        project.name,
        build_command=build_command,
        branch=branch,
        parent_command=parent_command,
        parent_branch=parent_branch,
    )

    cmd = dependency_install_command(project, version=node_ver)
    env = _node_env(version=node_ver)

    logger.info("Installing dependencies (Node %s): %s (in %s)", node_ver, cmd, project)

    try:
        result = run_process_stream(
            cmd,
            cwd=project,
            env=env,
            on_line=on_line,
            timeout=300,  # 5 minute timeout
        )
        if result.returncode != 0:
            stdout_text = result.stdout or ""
            # Auto-recovery for Windows ENOENT / -4058 directory lock/race issues
            if "-4058" in stdout_text or ("ENOENT" in stdout_text and "@nodelib" in stdout_text):
                if on_line:
                    on_line("⚠️ 检测到 Windows 解压并发冲突 (ENOENT -4058)，正在自动清理 node_modules 并重试...")
                logger.warning("Cleaning node_modules and retrying due to ENOENT -4058 for %s", project)
                import shutil
                if node_modules.is_dir():
                    shutil.rmtree(node_modules, ignore_errors=True)
                result = run_process_stream(
                    cmd,
                    cwd=project,
                    env=env,
                    on_line=on_line,
                    timeout=300,
                )

            if result.returncode != 0 and attempt_npmmirror_auto_sync(stdout_text, on_line=on_line):
                if on_line:
                    on_line("🔁 依赖同步完成，正在重新执行依赖安装...")
                logger.info("Retrying dependency install after npmmirror sync for %s", project)
                result = run_process_stream(
                    cmd,
                    cwd=project,
                    env=env,
                    on_line=on_line,
                    timeout=300,
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

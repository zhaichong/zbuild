# -*- coding: utf-8 -*-
"""Individual step functions for the workflow pipeline.

Each function takes a ``StepContext`` and returns a ``StepResult``.
"""

import logging
import importlib.util
import shutil
import threading
import time
from pathlib import Path
from typing import List, Optional

from workflow.steps import StepContext, StepResult
from core.errors import ToolError, BuildError, GitError, DependencyError, UploadError

logger = logging.getLogger(__name__)

# When multiple projects run in parallel, serialize the upload phase so
# concurrent SVN commits / SFTP deployments cannot race on the same
# repository or server target.  Builds stay parallel; only uploads queue up.
UPLOAD_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# Step: Check tools
# ---------------------------------------------------------------------------

def step_check_tools(ctx: StepContext) -> StepResult:
    """Verify that required tools (git, bash, svn) are available."""
    import os
    from tools.detect import detect_tools

    tools = detect_tools(config=ctx.config)
    ctx.tools = tools

    missing: List[str] = []

    git_path = tools.get("git", {}).get("path", "")
    if not git_path:
        missing.append("Git")
    else:
        # Propagate detected git path to safe_git() via environment variable
        os.environ["GIT_EXECUTABLE"] = git_path

    bash_path = tools.get("bash", {}).get("path", "")
    if not bash_path:
        missing.append("Bash")

    svn_path = tools.get("svn", {}).get("path", "")
    if ctx.mode == "svn":
        if not svn_path:
            missing.append("SVN")
        else:
            # Propagate detected svn path to _svn_exe() via config key
            ctx.config["svn_exe"] = svn_path
    elif svn_path:
        # If SVN exists but mode is local/server, propagate it but do not require it
        ctx.config["svn_exe"] = svn_path

    if ctx.mode == "server" and importlib.util.find_spec("paramiko") is None:
        missing.append("Python 包 paramiko")

    node_path = tools.get("node", {}).get("path", "")
    if node_path:
        node_dir = str(Path(node_path).parent)
        curr_path = os.environ.get("PATH", "")
        if node_dir not in curr_path.split(os.path.pathsep):
            os.environ["PATH"] = node_dir + os.path.pathsep + curr_path

    if missing:
        return StepResult(
            success=False,
            message=f"缺少工具: {', '.join(missing)}",
        )

    return StepResult(success=True, message="工具检查通过")


# ---------------------------------------------------------------------------
# Step: Switch branch
# ---------------------------------------------------------------------------

def step_switch_branch(ctx: StepContext) -> StepResult:
    """Switch the project to the target branch."""
    from git.branches import read_current_branch, ensure_branch

    # Record the original branch before any checkout
    original_branch = read_current_branch(ctx.project_path)
    ctx.extra["original_branch"] = original_branch

    if not ctx.branch:
        return StepResult(success=True, message="未指定分支，跳过切换")

    allow_stash = ctx.config.get("allow_stash", True)
    result = ensure_branch(ctx.project_path, ctx.branch, allow_stash=allow_stash)
    if isinstance(result, dict) and result.get("blocked"):
        return StepResult(
            success=False,
            message=f"分支切换被阻止，存在 {result.get('file_count', 0)} 个本地变更文件",
        )
    if not result:
        return StepResult(
            success=False,
            message=f"无法切换到分支: {ctx.branch}",
        )
    if isinstance(result, dict) and result.get("stashed"):
        ctx.extra["stashed"] = True
        return StepResult(
            success=True,
            message=f"已切换到分支: {ctx.branch}（已自动 stash {result.get('file_count', 0)} 个文件）",
        )
    return StepResult(success=True, message=f"已切换到分支: {ctx.branch}")


# ---------------------------------------------------------------------------
# Step: Pull latest
# ---------------------------------------------------------------------------

def step_pull_latest(ctx: StepContext) -> StepResult:
    """Pull the latest code for the current branch."""
    if not ctx.config.get("auto_pull", True):
        return StepResult(success=True, message="跳过拉取（已禁用）")

    from git.sync import pull_latest, latest_commit_info, sync_micro_frontend_siblings
    from runner.protocol import emit_log

    ok, message = pull_latest(ctx.project_path)
    if not ok:
        return StepResult(success=False, message=f"拉取失败: {message}")

    # Micro-frontend auto-synchronization: sync sibling micro repos (e.g. yarward-micro-menu, yarward-nova-ai)
    try:
        sync_micro_frontend_siblings(
            ctx.project_path,
            target_branch=ctx.branch,
            on_line=lambda line: emit_log(line, project=ctx.project_name),
        )
    except Exception as exc:
        logger.warning("Micro-frontend sibling sync skipped for %s: %s", ctx.project_name, exc)

    # Log latest commit info for traceability
    try:
        info = latest_commit_info(ctx.project_path)
        if info.get("sha"):
            commit_msg = f"最新提交 {info['sha'][:8]} {info['author']} {info['message'][:50]}"
            return StepResult(success=True, message=f"{message} | {commit_msg}")
    except Exception:
        pass
    return StepResult(success=True, message=message)


# ---------------------------------------------------------------------------
# Step: Install dependencies
# ---------------------------------------------------------------------------

def step_install_deps(ctx: StepContext) -> StepResult:
    """Install project dependencies if needed."""
    if not ctx.config.get("auto_install_deps", True):
        return StepResult(success=True, message="跳过依赖安装（已禁用）")

    from git.deps import ensure_dependencies
    from runner.protocol import emit
    from git.build_cmd import resolve_branch_build_command

    build_cmd = (
        ctx.extra.get("build_command")
        or resolve_branch_build_command(ctx.config, ctx.project_name, ctx.branch)
    )

    try:
        ensure_dependencies(
            ctx.project_path,
            build_command=build_cmd,
            branch=ctx.branch,
            on_line=lambda line: emit("log", {"level": "info", "message": line, "project": ctx.project_name}),
        )
        return StepResult(success=True, message="依赖安装完成")
    except DependencyError as exc:
        return StepResult(success=False, message=f"依赖安装失败: {exc}")


# ---------------------------------------------------------------------------
# Step: Build
# ---------------------------------------------------------------------------

def step_build(ctx: StepContext) -> StepResult:
    """Run configured build command/script to build the project, with optional build cache."""
    from git.build import build_project
    from runner.protocol import emit, emit_log

    from git.build_cmd import resolve_branch_build_command

    bash_val = ctx.tools.get("bash", "bash")
    bash_path = bash_val.get("path", "bash") if isinstance(bash_val, dict) else str(bash_val or "bash")
    build_cmd = (
        ctx.extra.get("build_command")
        or resolve_branch_build_command(ctx.config, ctx.project_name, ctx.branch)
    )
    artifact_paths = (
        ctx.extra.get("artifact_paths")
        or ctx.config.get("project_artifact_paths", {}).get(ctx.project_name)
        or ctx.config.get("artifact_paths")
        or ["dist"]
    )
    use_cache = ctx.config.get("use_build_cache", True)

    input_hash = ""
    cache = None
    if use_cache:
        from workflow.cache import BuildCache
        cache = BuildCache()
        input_hash = cache.compute_input_hash(ctx.project_path, build_command=build_cmd)
        logger.info("Build input hash for %s: %s", ctx.project_name, input_hash[:12])
        cached_artifact = cache.get_cached_artifact(input_hash)
        if cached_artifact:
            ctx.artifact_path = cached_artifact
            emit_log(f"⚡ 构建产物缓存命中 (Commit/配置未变)，0秒跳过Webpack编译: {cached_artifact.name}", project=ctx.project_name)
            return StepResult(
                success=True,
                message=f"⚡ 缓存命中，跳过编译: {cached_artifact.name}",
                context_updates={"artifact_path": str(cached_artifact)},
            )

    # Perform actual build via configured build_command
    try:
        emit_log(f"开始执行 {build_cmd} 构建项目 {ctx.project_name} ...", project=ctx.project_name)
        result, artifact = build_project(
            ctx.project_path,
            bash_exe=bash_path,
            build_command=build_cmd,
            target_branch=ctx.branch,
            artifact_paths=artifact_paths,
            on_line=lambda line: emit("log", {"level": "info", "message": line, "project": ctx.project_name}),
        )
        if artifact:
            if use_cache and cache and input_hash and artifact.is_file():
                try:
                    cache.store_artifact(input_hash, artifact)
                except Exception as exc:
                    logger.debug("Failed to store artifact in cache: %s", exc)
            ctx.artifact_path = artifact
            emit_log(f"构建完成，生成产物: {artifact.name}", project=ctx.project_name)
            return StepResult(
                success=True,
                message=f"打包完成: {artifact.name}",
                context_updates={"artifact_path": str(artifact)},
            )
        return StepResult(
            success=False,
            message="打包完成但未找到产物压缩包",
        )
    except BuildError as exc:
        return StepResult(success=False, message=f"打包失败: {exc}")


# ---------------------------------------------------------------------------
# Step: Select artifact
# ---------------------------------------------------------------------------

def step_select_artifact(ctx: StepContext) -> StepResult:
    """Select the latest tarball in candidate paths as the build artifact."""
    from git.build import latest_artifact

    if ctx.artifact_path and ctx.artifact_path.is_file():
        return StepResult(
            success=True,
            message=f"已选择产物: {ctx.artifact_path.name}",
        )

    artifact_paths = (
        ctx.extra.get("artifact_paths")
        or ctx.config.get("project_artifact_paths", {}).get(ctx.project_name)
        or ctx.config.get("artifact_paths")
        or ["dist"]
    )
    artifact = latest_artifact(ctx.project_path, candidate_paths=artifact_paths)
    if artifact:
        ctx.artifact_path = artifact
        return StepResult(
            success=True,
            message=f"已选择产物: {artifact.name}",
            context_updates={"artifact_path": str(artifact)},
        )
    return StepResult(success=False, message="未找到构建产物")


# ---------------------------------------------------------------------------
# Step: Upload to SVN
# ---------------------------------------------------------------------------

def step_upload_svn(ctx: StepContext) -> StepResult:
    """Upload the artifact to SVN."""
    from uploaders.svn import SvnUploader
    from runner.protocol import emit_log

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可上传的产物")

    uploader = SvnUploader()
    try:
        log_fn = lambda msg: emit_log(msg, project=ctx.project_name)
        with UPLOAD_LOCK:
            result = uploader.upload(ctx.artifact_path, ctx.config, log_fn, ctx.project_name)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=result.message or f"已上传到 SVN: {result.target_url}",
                context_updates={"target_url": result.target_url},
            )
        return StepResult(success=False, message=f"SVN 上传失败: {result.message}")
    except UploadError as exc:
        return StepResult(success=False, message=f"SVN 上传异常: {exc}")


# ---------------------------------------------------------------------------
# Step: Upload to server
# ---------------------------------------------------------------------------

def step_upload_server(ctx: StepContext) -> StepResult:
    """Upload the artifact to the target server via SSH/SFTP."""
    from uploaders.server import ServerUploader
    from runner.protocol import emit_log

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可上传的产物")

    uploader = ServerUploader()
    try:
        log_fn = lambda msg: emit_log(msg, project=ctx.project_name)
        with UPLOAD_LOCK:
            result = uploader.upload(ctx.artifact_path, ctx.config, log_fn, ctx.project_name)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=result.message or f"已上传到服务器: {result.target_url}",
                context_updates={"target_url": result.target_url},
            )
        return StepResult(success=False, message=f"服务器上传失败: {result.message}")
    except UploadError as exc:
        return StepResult(success=False, message=f"服务器上传异常: {exc}")


# ---------------------------------------------------------------------------
# Step: Copy to local output
# ---------------------------------------------------------------------------

def step_copy_local(ctx: StepContext) -> StepResult:
    """Copy the artifact to the local output directory."""
    from uploaders.local import LocalUploader
    from runner.protocol import emit_log

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可复制的产物")

    uploader = LocalUploader()
    try:
        log_fn = lambda msg: emit_log(msg, project=ctx.project_name)
        result = uploader.upload(ctx.artifact_path, ctx.config, log_fn, ctx.project_name)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=result.message or f"已复制到: {result.target_url}",
                context_updates={"target_url": result.target_url},
            )
        return StepResult(success=False, message=f"本地复制失败: {result.message}")
    except UploadError as exc:
        return StepResult(success=False, message=f"本地复制异常: {exc}")

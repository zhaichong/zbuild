# -*- coding: utf-8 -*-
"""Individual step functions for the workflow pipeline.

Each function takes a ``StepContext`` and returns a ``StepResult``.
"""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Optional

from workflow.steps import StepContext, StepResult
from core.errors import ToolError, BuildError, GitError, DependencyError, UploadError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step: Check tools
# ---------------------------------------------------------------------------

def step_check_tools(ctx: StepContext) -> StepResult:
    """Verify that required tools (git, bash, svn) are available."""
    from tools.detect import detect_tools

    tools = detect_tools()
    ctx.tools = tools

    missing: list[str] = []

    if not tools.get("git", {}).get("path"):
        missing.append("Git")
    if not tools.get("bash", {}).get("path"):
        missing.append("Bash")

    if ctx.mode == "svn" or ctx.mode == "local":
        if not tools.get("svn", {}).get("path"):
            missing.append("SVN")

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
    from git.branches import ensure_branch

    if not ctx.branch:
        return StepResult(success=True, message="未指定分支，跳过切换")

    ok = ensure_branch(ctx.project_path, ctx.branch)
    if not ok:
        return StepResult(
            success=False,
            message=f"无法切换到分支: {ctx.branch}",
        )
    return StepResult(success=True, message=f"已切换到分支: {ctx.branch}")


# ---------------------------------------------------------------------------
# Step: Pull latest
# ---------------------------------------------------------------------------

def step_pull_latest(ctx: StepContext) -> StepResult:
    """Pull the latest code for the current branch."""
    if not ctx.config.get("auto_pull", True):
        return StepResult(success=True, message="跳过拉取（已禁用）")

    from git.sync import pull_latest

    ok, message = pull_latest(ctx.project_path)
    if not ok:
        return StepResult(success=False, message=f"拉取失败: {message}")
    return StepResult(success=True, message=message)


# ---------------------------------------------------------------------------
# Step: Install dependencies
# ---------------------------------------------------------------------------

def step_install_deps(ctx: StepContext) -> StepResult:
    """Install project dependencies if needed."""
    if not ctx.config.get("auto_install_deps", True):
        return StepResult(success=True, message="跳过依赖安装（已禁用）")

    from git.deps import ensure_dependencies

    try:
        ensure_dependencies(ctx.project_path)
        return StepResult(success=True, message="依赖安装完成")
    except DependencyError as exc:
        return StepResult(success=False, message=f"依赖安装失败: {exc}")


# ---------------------------------------------------------------------------
# Step: Build
# ---------------------------------------------------------------------------

def step_build(ctx: StepContext) -> StepResult:
    """Run deploy.sh to build the project."""
    from git.build import build_project

    bash_path = ctx.tools.get("bash", {}).get("path", "bash")

    try:
        result, artifact = build_project(
            ctx.project_path,
            bash_exe=bash_path,
        )
        if artifact:
            ctx.artifact_path = artifact
            return StepResult(
                success=True,
                message=f"打包完成: {artifact.name}",
                context_updates={"artifact_path": str(artifact)},
            )
        return StepResult(
            success=False,
            message="打包完成但未找到产物 (dist/*.tar.gz)",
        )
    except BuildError as exc:
        return StepResult(success=False, message=f"打包失败: {exc}")


# ---------------------------------------------------------------------------
# Step: Select artifact
# ---------------------------------------------------------------------------

def step_select_artifact(ctx: StepContext) -> StepResult:
    """Select the latest dist/*.tar.gz as the build artifact."""
    from git.build import latest_artifact

    if ctx.artifact_path and ctx.artifact_path.is_file():
        return StepResult(
            success=True,
            message=f"已选择产物: {ctx.artifact_path.name}",
        )

    artifact = latest_artifact(ctx.project_path)
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

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可上传的产物")

    uploader = SvnUploader()
    try:
        result = uploader.upload(ctx.artifact_path, ctx.config, logger)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=f"已上传到 SVN: {result.target_url}",
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

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可上传的产物")

    uploader = ServerUploader()
    try:
        result = uploader.upload(ctx.artifact_path, ctx.config, logger)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=f"已上传到服务器: {result.target_url}",
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

    if not ctx.artifact_path:
        return StepResult(success=False, message="没有可复制的产物")

    uploader = LocalUploader()
    try:
        result = uploader.upload(ctx.artifact_path, ctx.config, logger)
        if result.success:
            ctx.target_url = result.target_url
            return StepResult(
                success=True,
                message=f"已复制到: {result.target_url}",
                context_updates={"target_url": result.target_url},
            )
        return StepResult(success=False, message=f"本地复制失败: {result.message}")
    except UploadError as exc:
        return StepResult(success=False, message=f"本地复制异常: {exc}")

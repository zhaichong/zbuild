# -*- coding: utf-8 -*-
"""Step definitions and context for the declarative workflow engine.

Inspired by Argo Workflows: each mode (svn/server/local) defines an
ordered list of ``StepDefinition`` objects that the Pipeline executes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.models import StepStatus


# ---------------------------------------------------------------------------
# Step context - shared state passed through the step chain
# ---------------------------------------------------------------------------

@dataclass
class StepContext:
    """Mutable context passed between steps during a single project run.

    Carries project info, configuration, detected tools, and intermediate
    results (e.g. the built artifact path).
    """
    project_name: str
    project_path: Path
    branch: str
    mode: str  # "svn" | "server" | "local"
    config: Dict[str, Any] = field(default_factory=dict)
    tools: Dict[str, Any] = field(default_factory=dict)
    artifact_path: Optional[Path] = None
    target_url: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Step result
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    """Return value from a step function."""
    success: bool
    message: str = ""
    skip_remaining: bool = False
    context_updates: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Step definition (Argo-style declarative step)
# ---------------------------------------------------------------------------

@dataclass
class StepDefinition:
    """Declarative definition of a single workflow step.

    Attributes
    ----------
    name:
        Human-readable step name (shown in the UI).
    fn:
        The callable ``(StepContext) -> StepResult``.
    max_retries:
        Number of retry attempts on failure (0 = no retry).
    retry_delay:
        Base delay in seconds between retries (doubles each attempt).
    skip_if:
        Optional callable ``(StepContext) -> bool``.  If it returns True
        the step is skipped.
    """
    name: str
    fn: Callable[[StepContext], StepResult]
    max_retries: int = 0
    retry_delay: float = 2.0
    skip_if: Optional[Callable[[StepContext], bool]] = None


# ---------------------------------------------------------------------------
# Step chain per mode
# ---------------------------------------------------------------------------

def get_steps(mode: str) -> List[StepDefinition]:
    """Return the ordered step chain for the given mode.

    Parameters
    ----------
    mode:
        One of "svn", "server", "local".

    Returns
    -------
    List[StepDefinition]:
        The step chain to execute.
    """
    from workflow.step_fns import (
        step_check_tools,
        step_switch_branch,
        step_pull_latest,
        step_install_deps,
        step_build,
        step_select_artifact,
        step_upload_svn,
        step_upload_server,
        step_copy_local,
    )

    if mode == "server":
        return [
            StepDefinition(name="检查 Git/Bash 工具", fn=step_check_tools, max_retries=0),
            StepDefinition(name="切换 Git 分支", fn=step_switch_branch, max_retries=1),
            StepDefinition(name="拉取当前分支最新代码", fn=step_pull_latest, max_retries=2, retry_delay=3.0),
            StepDefinition(name="检查并安装项目依赖", fn=step_install_deps, max_retries=1),
            StepDefinition(name="执行项目打包", fn=step_build, max_retries=1),
            StepDefinition(name="选择最新 dist/*.tar.gz", fn=step_select_artifact, max_retries=0),
            StepDefinition(name="上传产物到服务器", fn=step_upload_server, max_retries=3, retry_delay=5.0),
        ]
    elif mode == "local":
        return [
            StepDefinition(name="检查 Git/Bash/SVN 工具", fn=step_check_tools, max_retries=0),
            StepDefinition(name="切换 Git 分支", fn=step_switch_branch, max_retries=1),
            StepDefinition(name="拉取当前分支最新代码", fn=step_pull_latest, max_retries=2, retry_delay=3.0),
            StepDefinition(name="检查并安装项目依赖", fn=step_install_deps, max_retries=1),
            StepDefinition(name="执行项目打包", fn=step_build, max_retries=1),
            StepDefinition(name="选择最新 dist/*.tar.gz", fn=step_select_artifact, max_retries=0),
            StepDefinition(name="跳过 SVN，准备本地输出", fn=lambda ctx: StepResult(success=True, message="Local mode"), max_retries=0),
            StepDefinition(name="复制产物到本地输出目录", fn=step_copy_local, max_retries=1),
            StepDefinition(name="本地打包完成", fn=lambda ctx: StepResult(success=True, message="Done"), max_retries=0),
        ]
    else:
        # Default: svn mode
        return [
            StepDefinition(name="检查 Git/Bash/SVN 工具", fn=step_check_tools, max_retries=0),
            StepDefinition(name="切换 Git 分支", fn=step_switch_branch, max_retries=1),
            StepDefinition(name="拉取当前分支最新代码", fn=step_pull_latest, max_retries=2, retry_delay=3.0),
            StepDefinition(name="检查并安装项目依赖", fn=step_install_deps, max_retries=1),
            StepDefinition(name="执行项目打包", fn=step_build, max_retries=1),
            StepDefinition(name="选择最新 dist/*.tar.gz", fn=step_select_artifact, max_retries=0),
            StepDefinition(name="上传产物到 SVN", fn=step_upload_svn, max_retries=2, retry_delay=5.0),
        ]

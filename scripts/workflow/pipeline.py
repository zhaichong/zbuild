# -*- coding: utf-8 -*-
"""Pipeline orchestrator.

Replaces the monolithic HeadlessWorkflow with a step-based pipeline
that supports retry, per-project execution, and execution recording.
"""
from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from core.models import (
    StepStatus,
    StepRecord,
    LogEntry,
    BuildArtifact,
    ProjectRunRecord,
    ExecutionRecord,
)
from core.history import HistoryStore
from core.config import load_config
from runner.protocol import emit, emit_log, emit_step_start, emit_step_end, emit_result
from workflow.steps import StepContext, StepDefinition, StepResult, get_steps

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the build-and-upload pipeline for one or more projects.

    Parameters
    ----------
    payload:
        The full run configuration from the Electron frontend.
        Must contain at least ``mode`` and ``projects``.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.config = load_config()
        # Override config with payload values
        self.config.update({k: v for k, v in payload.items() if v is not None})
        self.mode = self.config.get("mode", "svn")
        self.history_store = HistoryStore()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_payload(self) -> None:
        """Validate the payload before execution."""
        if self.mode not in ("svn", "server", "local"):
            raise ValueError(f"Invalid mode: {self.mode}")

        projects = self.config.get("projects", [])
        if not projects:
            raise ValueError("No projects configured for this run")

        for proj in projects:
            if not proj.get("name"):
                raise ValueError("Each project must have a 'name'")
            if not proj.get("path"):
                raise ValueError(f"Project '{proj.get('name')}' must have a 'path'")

    # ------------------------------------------------------------------
    # Single step execution with retry
    # ------------------------------------------------------------------

    def _run_step(
        self,
        step_def: StepDefinition,
        ctx: StepContext,
        step_index: int,
    ) -> StepRecord:
        """Execute a single step with retry and exponential backoff.

        Returns a ``StepRecord`` with the execution details.
        """
        record = StepRecord(
            name=step_def.name,
            status=StepStatus.PENDING,
            max_retries=step_def.max_retries,
        )

        # Check skip condition
        if step_def.skip_if and step_def.skip_if(ctx):
            record.status = StepStatus.SKIPPED
            record.message = "Skipped by condition"
            emit_step_end(step_def.name, True, "Skipped", step_index)
            return record

        max_attempts = 1 + step_def.max_retries
        delay = step_def.retry_delay

        for attempt in range(1, max_attempts + 1):
            record.attempts = attempt
            record.started_at = time.time()

            if attempt > 1:
                record.status = StepStatus.RETRYING
                emit_log(f"重试 {step_def.name} (第 {attempt} 次)", level="warn")
            else:
                record.status = StepStatus.RUNNING

            emit_step_start(step_def.name, step_index)

            try:
                result = step_def.fn(ctx)
            except Exception as exc:
                record.status = StepStatus.FAILED
                record.message = f"异常: {exc}"
                record.finished_at = time.time()
                record.duration_seconds = record.finished_at - (record.started_at or 0)
                record.logs.append(LogEntry(
                    timestamp=time.time(),
                    level="error",
                    message=str(exc),
                ))
                emit_step_end(step_def.name, False, str(exc), step_index)
                emit_log(f"{step_def.name} 异常: {exc}", level="error")

                if attempt < max_attempts:
                    emit_log(f"等待 {delay:.1f}s 后重试...", level="info")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                    continue
                return record

            record.finished_at = time.time()
            record.duration_seconds = record.finished_at - (record.started_at or 0)

            if result.success:
                record.status = StepStatus.SUCCESS
                record.message = result.message
                # Apply context updates
                if result.context_updates:
                    for key, val in result.context_updates.items():
                        if key == "artifact_path" and val:
                            ctx.artifact_path = Path(val)
                        elif key == "target_url":
                            ctx.target_url = val
                        else:
                            ctx.extra[key] = val

                emit_step_end(step_def.name, True, result.message, step_index)
                return record
            else:
                record.message = result.message
                record.logs.append(LogEntry(
                    timestamp=time.time(),
                    level="error",
                    message=result.message,
                ))
                emit_step_end(step_def.name, False, result.message, step_index)
                emit_log(f"{step_def.name} 失败: {result.message}", level="error")

                if attempt < max_attempts:
                    emit_log(f"等待 {delay:.1f}s 后重试...", level="info")
                    time.sleep(delay)
                    delay *= 2
                    continue

                record.status = StepStatus.FAILED
                return record

        # Should not reach here, but just in case
        record.status = StepStatus.FAILED
        return record

    # ------------------------------------------------------------------
    # Single project execution
    # ------------------------------------------------------------------

    def run_one(self, project_config: dict[str, Any]) -> ProjectRunRecord:
        """Execute the full step chain for a single project.

        Returns a ``ProjectRunRecord`` with all step results.
        """
        name = project_config["name"]
        project_path = Path(project_config["path"])
        branch = project_config.get("branch", "")

        emit_log(f"开始处理项目: {name} (分支: {branch})")

        proj_record = ProjectRunRecord(
            project_name=name,
            branch=branch,
            started_at=time.time(),
        )

        ctx = StepContext(
            project_name=name,
            project_path=project_path,
            branch=branch,
            mode=self.mode,
            config=self.config,
        )

        steps = get_steps(self.mode)
        all_ok = True

        for idx, step_def in enumerate(steps):
            step_record = self._run_step(step_def, ctx, idx)
            proj_record.steps.append(step_record)

            if step_record.status == StepStatus.FAILED:
                all_ok = False
                proj_record.error_message = step_record.message
                emit_log(f"项目 {name} 在步骤 '{step_def.name}' 失败: {step_record.message}", level="error")
                break

            if step_record.status == StepStatus.SKIPPED:
                continue

        proj_record.finished_at = time.time()
        proj_record.success = all_ok
        proj_record.target_url = ctx.target_url

        if ctx.artifact_path:
            artifact = BuildArtifact(
                path=str(ctx.artifact_path),
                created_at=ctx.artifact_path.stat().st_mtime if ctx.artifact_path.exists() else 0,
            )
            artifact.compute_hash()
            proj_record.artifact = artifact

        status_str = "成功" if all_ok else "失败"
        emit_log(f"项目 {name} 处理{status_str}")
        return proj_record

    # ------------------------------------------------------------------
    # Full pipeline execution
    # ------------------------------------------------------------------

    def run(self) -> ExecutionRecord:
        """Execute the pipeline for all configured projects.

        Returns the complete ``ExecutionRecord``.
        """
        self._validate_payload()

        run_id = uuid.uuid4().hex[:12]
        record = ExecutionRecord(
            run_id=run_id,
            mode=self.mode,
            started_at=time.time(),
            config_snapshot=self.config.copy(),
        )

        emit_log(f"=== 开始执行 (模式: {self.mode}, 运行ID: {run_id}) ===")

        # Save initial record
        self.history_store.create(record)

        projects = self.config.get("projects", [])
        enabled_projects = [p for p in projects if p.get("enabled", True)]

        all_ok = True
        for proj_config in enabled_projects:
            proj_record = self.run_one(proj_config)
            record.projects.append(proj_record)
            if not proj_record.success:
                all_ok = False

        record.finished_at = time.time()
        record.success = all_ok

        # Update history with final state
        self.history_store.update(record)

        status_str = "成功" if all_ok else "失败"
        duration = record.duration_seconds
        emit_log(f"=== 执行{status_str} (耗时: {duration:.1f}s) ===")
        emit_result(all_ok, {
            "run_id": run_id,
            "duration": duration,
            "projects": [p.to_dict() for p in record.projects],
        })

        return record

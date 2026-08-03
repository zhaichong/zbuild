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
        # Deep merge payload into config (don't overwrite nested dicts)
        for k, v in payload.items():
            if v is None:
                continue
            if isinstance(v, dict) and isinstance(self.config.get(k), dict):
                self.config[k].update(v)
            else:
                self.config[k] = v

        # Override allow_stash with payload's stash field if present
        if "stash" in payload:
            self.config["allow_stash"] = payload["stash"]

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

        if not any(proj.get('enabled', True) for proj in projects):
            raise ValueError('No enabled projects configured for this run')

        for proj in projects:
            if not proj.get("name"):
                raise ValueError("Each project must have a 'name'")
            if not proj.get("path"):
                raise ValueError(f"Project '{proj.get('name')}' must have a 'path'")

        # Validate credentials based on mode
        if self.mode == "svn":
            svn_creds = self.config.get("svn_credentials", {})
            if not svn_creds.get("username") or not svn_creds.get("password"):
                raise ValueError("SVN mode requires username and password in svn_credentials")
            if not self.config.get("svn_root"):
                raise ValueError("SVN mode requires svn_root URL")
            if not self.config.get("hospital_name"):
                raise ValueError("SVN mode requires hospital_name")
            if not self.config.get("order_no"):
                raise ValueError("SVN mode requires order_no")
        elif self.mode == "server":
            server = self.config.get("server", {})
            if not server.get("host"):
                raise ValueError("Server mode requires server host address")
            if not server.get("username") or not server.get("password"):
                raise ValueError("Server mode requires server username and password")
            configured_paths = self.config.get("server_upload_paths", {})
            missing_paths = [
                proj["name"]
                for proj in projects
                if proj.get("enabled", True)
                and not proj.get("server_upload_path")
                and not configured_paths.get(proj["name"])
            ]
            if missing_paths:
                raise ValueError(
                    "Server mode requires an upload path for: " + ", ".join(missing_paths)
                )

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
            emit_step_end(step_def.name, True, "Skipped", step_index, project=ctx.project_name)
            return record

        max_attempts = 1 + step_def.max_retries
        delay = step_def.retry_delay

        for attempt in range(1, max_attempts + 1):
            record.attempts = attempt
            record.started_at = time.time()

            if attempt > 1:
                record.status = StepStatus.RETRYING
                emit_log(f"重试 {step_def.name} (第 {attempt} 次)", level="warning", project=ctx.project_name)
            else:
                record.status = StepStatus.RUNNING

            emit_step_start(step_def.name, step_index, project=ctx.project_name)

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
                emit_step_end(step_def.name, False, str(exc), step_index, project=ctx.project_name)
                emit_log(f"{step_def.name} 异常: {exc}", level="error", project=ctx.project_name)

                if attempt < max_attempts:
                    emit_log(f"等待 {delay:.1f}s 后重试...", level="info", project=ctx.project_name)
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

                emit_step_end(step_def.name, True, result.message, step_index, project=ctx.project_name)
                return record
            else:
                record.message = result.message
                record.logs.append(LogEntry(
                    timestamp=time.time(),
                    level="error",
                    message=result.message,
                ))
                emit_step_end(step_def.name, False, result.message, step_index, project=ctx.project_name)
                emit_log(f"{step_def.name} 失败: {result.message}", level="error", project=ctx.project_name)

                if attempt < max_attempts:
                    emit_log(f"等待 {delay:.1f}s 后重试...", level="info", project=ctx.project_name)
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

        steps = get_steps(self.mode)
        step_names = [s.name for s in steps]

        emit_log(f"开始处理项目: {name} (分支: {branch})", project=name)
        emit("projectStart", {"project": name, "steps": step_names})

        proj_record = ProjectRunRecord(
            project_name=name,
            branch=branch,
            started_at=time.time(),
        )

        build_command = (
            project_config.get("build_command")
            or project_config.get("buildCommand")
            or self.config.get("build_commands", {}).get(name)
            or self.config.get("build_command")
            or self.config.get("buildCommand")
            or "deploy.sh"
        )

        ctx = StepContext(
            project_name=name,
            project_path=project_path,
            branch=branch,
            mode=self.mode,
            config=self.config,
            extra={"build_command": build_command},
        )

        steps = get_steps(self.mode)
        all_ok = True
        restore_error = ""

        try:
            for idx, step_def in enumerate(steps):
                step_record = self._run_step(step_def, ctx, idx)
                proj_record.steps.append(step_record)

                if step_record.status == StepStatus.FAILED:
                    all_ok = False
                    proj_record.error_message = step_record.message
                    emit_log(f"项目 {name} 在步骤 '{step_def.name}' 失败: {step_record.message}", level="error", project=name)
                    break

                if step_record.status == StepStatus.SKIPPED:
                    continue
        finally:
            # Only restore original branch if explicitly configured (disabled by default)
            if self.config.get("restore_branch", False):
                original_branch = ctx.extra.get("original_branch")
                if original_branch:
                    emit_log(f"正在恢复项目 {name} 到原分支 {original_branch}...", project=name)
                    try:
                        from git.branches import read_current_branch, safe_git
                        from tools.exec import run_process
                        restored = True
                        if read_current_branch(ctx.project_path) != original_branch:
                            checkout = run_process(
                                safe_git(ctx.project_path) + ["checkout", original_branch]
                            )
                            restored = checkout.returncode == 0
                            if not restored:
                                restore_error = f"恢复原分支失败: {checkout.stderr or checkout.stdout}"
                                emit_log(f"项目 {name} {restore_error}", level="warning", project=name)
                        if restored and ctx.extra.get("stashed"):
                            # Clean up any working-tree changes left by a failed build
                            # (e.g. deploy.sh copies vue.config.js and may not restore it on error).
                            # We must discard these before stash pop, otherwise git will refuse
                            # to pop because the file would be overwritten.
                            run_process(safe_git(ctx.project_path) + ["checkout", "--", "."])
                            pop_res = run_process(safe_git(ctx.project_path) + ["stash", "pop"])
                            if pop_res.returncode == 0:
                                emit_log(f"成功还原项目 {name} 的本地修改。", project=name)
                            else:
                                restore_error = f"恢复本地修改失败: {pop_res.stderr or pop_res.stdout}"
                                emit_log(f"项目 {name} {restore_error}", level="warning", project=name)
                    except Exception as exc:
                        restore_error = f"恢复工作区异常: {exc}"
                        emit_log(f"项目 {name} {restore_error}", level="warning", project=name)

        if restore_error:
            all_ok = False
            proj_record.error_message = (
                f"{proj_record.error_message}; {restore_error}"
                if proj_record.error_message
                else restore_error
            )

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
        emit_log(f"项目 {name} 处理{status_str}", project=name)
        emit("projectResult", {
            "project": name,
            "success": all_ok,
            "message": proj_record.error_message or status_str,
        })
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

        # Auto-create order directory if configured and enabled
        order_dir_base = self.config.get("order_dir_path")
        form_cfg = self.config.get("form", {}) if isinstance(self.config.get("form"), dict) else {}
        create_enabled = self.config.get("create_order_dir") or form_cfg.get("createOrderDir") or form_cfg.get("create_order_dir")

        if order_dir_base and create_enabled:
            order_no = self.config.get("order_no") or form_cfg.get("orderNo") or form_cfg.get("order_no") or ""
            hospital_name = self.config.get("hospital_name") or form_cfg.get("hospitalName") or form_cfg.get("hospital_name") or ""
            if order_no and hospital_name:
                try:
                    from tools.order_dir import create_order_directory
                    enabled_projs = [p for p in self.config.get("projects", []) if p.get("enabled", True)]
                    res = create_order_directory(order_dir_base, str(order_no), str(hospital_name), enabled_projs)
                    if res.get("success"):
                        emit_log(f"{res.get('message')}", level="info")
                    else:
                        emit_log(f"创建提测目录失败: {res.get('message')}", level="warning")
                except Exception as e:
                    emit_log(f"创建提测目录异常: {e}", level="warning")

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

        success_count = sum(1 for p in record.projects if p.success)
        failure_count = len(record.projects) - success_count
        emit("done", {
            "total": len(record.projects),
            "successCount": success_count,
            "failureCount": failure_count,
        })

        emit_result(all_ok, {
            "run_id": run_id,
            "duration": duration,
            "projects": [p.to_dict() for p in record.projects],
        })

        return record

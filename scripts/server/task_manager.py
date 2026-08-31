# -*- coding: utf-8 -*-
"""Persistent FIFO task scheduler with bounded worker concurrency."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from server.task_store import TERMINAL_STATUSES, TaskStore

logger = logging.getLogger(__name__)
ALLOWED_TASK_TYPES = {"run", "order-deploy-run"}


class TaskManager:
    def __init__(self, store, runner, workspace, max_concurrency: int = 2):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        self.store: TaskStore = store
        self.runner = runner
        self.workspace = workspace
        self.max_concurrency = max_concurrency
        self._queue: asyncio.PriorityQueue[Tuple[int, str]] = asyncio.PriorityQueue()
        self._workers: List[asyncio.Task] = []
        self._active: Set[str] = set()
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._started = False
        self._maintenance_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._started:
            return
        self.store.recover_after_restart()
        for task_id in self.store.list_queued_ids():
            task = self.store.get_task(task_id, detail=False)
            if task:
                await self._queue.put((task["queueSeq"], task_id))
        self._workers = [
            asyncio.create_task(self._worker(), name=f"zbuild-worker-{index}")
            for index in range(self.max_concurrency)
        ]
        self._maintenance_task = asyncio.create_task(
            self._maintenance_loop(), name="zbuild-maintenance"
        )
        self._started = True

    async def shutdown(self) -> None:
        if not self._started:
            return
        for task_id in list(self._active):
            await self.runner.stop_run(task_id)
        for worker in self._workers:
            worker.cancel()
        if self._maintenance_task:
            self._maintenance_task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        if self._maintenance_task:
            await asyncio.gather(self._maintenance_task, return_exceptions=True)
            self._maintenance_task = None
        self._workers.clear()
        self._started = False

    async def submit_task(
        self, request_id: str, task_type: str, submitter: str, payload: Dict[str, Any],
        remote_ip: str = "", profile_id: str = "",
    ) -> Dict[str, Any]:
        if not self._started:
            raise RuntimeError("Task manager is not started")
        if task_type not in ALLOWED_TASK_TYPES:
            raise ValueError("Unsupported task type")
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 128:
            raise ValueError("requestId is required and must be at most 128 characters")
        if not isinstance(submitter, str) or not submitter.strip() or len(submitter.strip()) > 64:
            raise ValueError("submitter is required and must be at most 64 characters")
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        task, created = self.store.create_task(
            request_id.strip(), task_type, submitter.strip(), payload, profile_id
        )
        if created:
            event = self.store.append_event(task["taskId"], "status", {"status": "queued"})
            await self._publish(event)
            await self._queue.put((task["queueSeq"], task["taskId"]))
            self.store.record_audit(
                "task.create", "created", task_id=task["taskId"],
                submitter=submitter.strip(), remote_ip=remote_ip,
            )
        return task

    async def cancel_task(
        self, task_id: str, submitter: str = "", remote_ip: str = "", profile_id: str = "",
    ) -> Dict[str, Any]:
        task = self.store.request_cancel(task_id, profile_id)
        if task_id in self._active:
            await self.runner.stop_run(task_id)
        if task["status"] == "cancelled":
            event = self.store.append_event(task_id, "status", {"status": "cancelled"})
            await self._publish(event)
        self.store.record_audit(
            "task.cancel", task["status"], task_id=task_id,
            submitter=submitter, remote_ip=remote_ip,
        )
        return task

    async def _worker(self) -> None:
        while True:
            _, task_id = await self._queue.get()
            try:
                task = self.store.get_task(task_id, detail=False)
                if not task or task["status"] in TERMINAL_STATUSES:
                    continue
                await self._execute(task_id, task["type"])
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Task %s failed", task_id)
                await self._finish(
                    task_id, "failed",
                    error=f"Task preparation failed ({type(exc).__name__})",
                )
            finally:
                self._queue.task_done()

    async def _set_status(self, task_id: str, status: str, **kwargs) -> Dict[str, Any]:
        task = self.store.set_status(task_id, status, **kwargs)
        event = self.store.append_event(task_id, "status", {"status": task["status"]})
        await self._publish(event)
        return task

    async def _finish(
        self, task_id: str, status: str, *, error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.store.is_cancel_requested(task_id):
            status = "cancelled"
        await self._set_status(task_id, status, error=error, result=result)
        self.store.clear_execution_secrets(task_id)

    async def _execute(self, task_id: str, task_type: str) -> None:
        await self._set_status(task_id, "preparing")
        payload = self.store.get_execution_payload(task_id)
        commits: List[Dict[str, str]] = []
        if task_type == "run":
            payload, commits = await self.workspace.prepare(task_id, payload)
        if commits:
            self.store.set_commits(task_id, commits)
            event = self.store.append_event(task_id, "commits", {"items": commits})
            await self._publish(event)
        if self.store.is_cancel_requested(task_id):
            await self._finish(task_id, "cancelled")
            return

        self._active.add(task_id)
        await self._set_status(task_id, "running")
        final_result: Optional[Dict[str, Any]] = None

        async def on_event(payload_event: Dict[str, Any]):
            nonlocal final_result
            event_type = str(payload_event.get("type") or "event")
            if event_type == "result":
                final_result = payload_event
            event = self.store.append_event(task_id, event_type, payload_event)
            await self._publish(event)

        async def on_exit(_code: int):
            return None

        try:
            code = await self.runner.stream_run(
                task_type, payload, on_event, on_exit, task_id=task_id
            )
            success = code == 0 and (final_result is None or final_result.get("success", True))
            if final_result:
                for artifact in await self.workspace.collect_artifacts(task_id, final_result):
                    self.store.add_artifact(
                        task_id, artifact["name"], artifact["path"], artifact.get("mimeType")
                    )
            await self._finish(
                task_id, "success" if success else "failed",
                error=None if success else "Task process failed", result=final_result,
            )
        finally:
            self._active.discard(task_id)
            # Instantly clean up ephemeral task workspace to prevent disk bloat
            try:
                await self.workspace.cleanup(task_id)
            except Exception:
                logger.warning("Failed to instant-cleanup workspace for task %s", task_id, exc_info=True)

    async def _publish(self, event: Dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(event["taskId"], set())):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest item to make space for the latest step/status events
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:
                    self._subscribers[event["taskId"]].discard(queue)

    def subscribe(self, task_id: str) -> asyncio.Queue:
        if not self.store.get_task(task_id, detail=False):
            raise KeyError(task_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.setdefault(task_id, set()).add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(task_id)
        if subscribers:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(task_id, None)

    async def _maintenance_loop(self) -> None:
        while True:
            try:
                candidates = self.store.maintenance_candidates()
                for task_id in candidates["workspaceTaskIds"]:
                    try:
                        await self.workspace.cleanup(task_id)
                    except Exception:
                        logger.warning("Could not clean workspace for %s", task_id, exc_info=True)
                artifact_root_value = getattr(self.workspace, "artifact_root", None)
                if artifact_root_value:
                    artifact_root = artifact_root_value.resolve()
                    for raw_path in candidates["artifactPaths"]:
                        try:
                            path = Path(raw_path).resolve()
                            path.relative_to(artifact_root)
                            path.unlink(missing_ok=True)
                        except Exception:
                            logger.warning("Could not clean artifact %s", raw_path, exc_info=True)
                for task_id in candidates["expiredLogTaskIds"]:
                    (self.store.log_dir / f"{task_id}.ndjson").unlink(missing_ok=True)
                # Prune stale dependency cache slots
                if hasattr(self.workspace, "prune_deps_cache"):
                    try:
                        await self.workspace.prune_deps_cache()
                    except Exception:
                        logger.warning("Deps cache pruning failed", exc_info=True)
            except Exception:
                logger.warning("Task retention maintenance failed", exc_info=True)
            await asyncio.sleep(24 * 60 * 60)

# -*- coding: utf-8 -*-
"""Task runner service for Web/WebSocket execution with concurrency control."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
RUNNER_ENTRY = SCRIPTS_DIR / "electron_runner.py"

MAX_CONCURRENT_RUNS = 2
QUICK_COMMAND_TIMEOUT = 60


def _process_options() -> Dict[str, Any]:
    if os.name == "nt":
        return {"creationflags": getattr(__import__("subprocess"), "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


class TaskRunnerService:
    def __init__(self, max_concurrency: int = MAX_CONCURRENT_RUNS):
        self.max_concurrency = max_concurrency
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.running_count = 0
        self.queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Set[Any] = set()

    async def execute_command(self, command_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a quick command and return the final JSON result."""
        # For non-streaming quick commands, invoke runner directly or via subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(RUNNER_ENTRY),
            command_name,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(SCRIPTS_DIR.parent),
            **_process_options(),
        )
        input_data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data), timeout=QUICK_COMMAND_TIMEOUT
            )
        except asyncio.TimeoutError:
            await self._terminate_process_tree(process)
            return {"success": False, "error": "Command timed out"}

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        # Parse line-delimited JSON events to find the final result
        last_result = None
        for line in stdout_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if evt.get("type") == "result":
                    last_result = evt
                elif evt.get("type") == "error":
                    last_result = {"success": False, "error": evt.get("message", "Unknown error")}
            except json.JSONDecodeError:
                continue

        if last_result is not None:
            return last_result
        if process.returncode != 0:
            return {"success": False, "error": stderr_text or f"Command exited with code {process.returncode}"}
        return {"success": True, "output": stdout_text}

    async def stream_run(
        self,
        command_name: str,
        payload: Dict[str, Any],
        event_callback: Callable[[Dict[str, Any]], Any],
        exit_callback: Callable[[int], Any],
        task_id: str = "default",
    ) -> int:
        """Run a streaming pipeline command, piping line-by-line events to event_callback."""
        # Check concurrency
        if self.running_count >= self.max_concurrency:
            await event_callback({
                "type": "queue_status",
                "running": self.running_count,
                "message": f"任务已进入排队队列（当前运行中: {self.running_count}/{self.max_concurrency}）"
            })

        self.running_count += 1
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(RUNNER_ENTRY),
                command_name,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(SCRIPTS_DIR.parent),
                **_process_options(),
            )
            self.active_processes[task_id] = proc

            # Write stdin payload and close stdin
            input_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if proc.stdin:
                proc.stdin.write(input_bytes)
                await proc.stdin.drain()
                proc.stdin.close()

            # Read stdout stream line by line
            async def read_stdout():
                assert proc.stdout is not None
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if not line_str:
                        continue
                    try:
                        evt = json.loads(line_str)
                        await event_callback(evt)
                    except json.JSONDecodeError:
                        await event_callback({"type": "log", "level": "info", "message": line_str})

            async def read_stderr():
                assert proc.stderr is not None
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if not line_str:
                        continue
                    await event_callback({"type": "log", "level": "error", "message": line_str})

            await asyncio.gather(read_stdout(), read_stderr())
            ret_code = await proc.wait()
            await exit_callback(ret_code)
            return ret_code
        except Exception as exc:
            logger.error("Error during stream_run: %s", exc)
            await event_callback({"type": "error", "message": str(exc)})
            await exit_callback(1)
            return 1
        finally:
            self.active_processes.pop(task_id, None)
            self.running_count = max(0, self.running_count - 1)

    async def stop_run(self, task_id: str = "default") -> bool:
        """Terminate an active running task."""
        proc = self.active_processes.get(task_id)
        if proc and proc.returncode is None:
            try:
                await self._terminate_process_tree(proc)
                return True
            except ProcessLookupError:
                return True
            except Exception as e:
                logger.warning("Failed to kill process for task %s: %s", task_id, e)
                return False
        return False

    async def _terminate_process_tree(self, proc: asyncio.subprocess.Process) -> None:
        if proc.returncode is not None:
            return
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec(
                "taskkill", "/PID", str(proc.pid), "/T", "/F",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
        else:
            import signal
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


runner_service = TaskRunnerService()

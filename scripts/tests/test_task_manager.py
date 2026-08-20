# -*- coding: utf-8 -*-
"""Concurrency, FIFO, cancellation, and disconnect-independent task tests."""

import asyncio
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.secrets import SecretCodec
from server.task_manager import TaskManager
from server.task_store import TaskStore


class FakeCodec(SecretCodec):
    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext


class BlockingRunner:
    def __init__(self):
        self.started = []
        self.releases = {}
        self.active = 0
        self.max_seen = 0

    async def stream_run(self, command_name, payload, event_callback, exit_callback, task_id):
        self.started.append(task_id)
        self.active += 1
        self.max_seen = max(self.max_seen, self.active)
        release = self.releases.setdefault(task_id, asyncio.Event())
        await event_callback({"type": "log", "level": "info", "message": "started"})
        await release.wait()
        self.active -= 1
        await event_callback({"type": "result", "success": True, "projects": []})
        await exit_callback(0)
        return 0

    async def stop_run(self, task_id):
        self.releases.setdefault(task_id, asyncio.Event()).set()
        return True


class PassthroughWorkspace:
    async def prepare(self, task_id, payload):
        return payload, []

    async def collect_artifacts(self, task_id, result):
        return []

    async def cleanup(self, task_id):
        return None


async def wait_until(predicate, timeout=2.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError("condition was not reached")
        await asyncio.sleep(0.01)


class TestTaskManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.temp_dir.name), codec=FakeCodec())
        self.runner = BlockingRunner()
        self.manager = TaskManager(
            self.store, self.runner, PassthroughWorkspace(), max_concurrency=2
        )
        await self.manager.start()

    async def asyncTearDown(self):
        await self.manager.shutdown()
        self.store.close()
        self.temp_dir.cleanup()

    async def test_four_tasks_are_strict_fifo_with_at_most_two_running(self):
        tasks = [
            await self.manager.submit_task(f"req-{index}", "run", "alice", {})
            for index in range(4)
        ]
        ids = [task["taskId"] for task in tasks]

        await wait_until(lambda: len(self.runner.started) == 2)
        self.assertEqual(self.runner.started, ids[:2])
        self.assertEqual(self.runner.max_seen, 2)

        self.runner.releases[ids[0]].set()
        await wait_until(lambda: len(self.runner.started) == 3)
        self.assertEqual(self.runner.started[2], ids[2])

        await self.manager.cancel_task(ids[3], "alice", "127.0.0.1")
        self.assertEqual(self.store.get_task(ids[3])["status"], "cancelled")

        for task_id in ids[:3]:
            self.runner.releases.setdefault(task_id, asyncio.Event()).set()
        await wait_until(lambda: all(
            self.store.get_task(task_id)["status"] == "success" for task_id in ids[:3]
        ))
        self.assertEqual(self.runner.started, ids[:3])

    async def test_cancelling_running_task_wins_over_natural_exit(self):
        task = await self.manager.submit_task("req-cancel", "run", "bob", {})
        task_id = task["taskId"]
        await wait_until(lambda: task_id in self.runner.started)

        await self.manager.cancel_task(task_id, "bob", "127.0.0.1")
        await wait_until(lambda: self.store.get_task(task_id)["status"] == "cancelled")

        self.assertEqual(self.store.get_task(task_id)["status"], "cancelled")
        events = self.store.list_events(task_id)
        self.assertTrue(any(event["type"] == "status" for event in events))


if __name__ == "__main__":
    unittest.main()

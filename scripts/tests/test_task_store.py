# -*- coding: utf-8 -*-
"""Behavior tests for persistent Web task state and secret redaction."""

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.task_store import TaskStore
from server.secrets import SecretCodec, merge_secrets, split_secrets


class FakeCodec(SecretCodec):
    def encrypt(self, plaintext: str) -> str:
        return "encrypted:" + plaintext

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext.startswith("encrypted:"):
            raise ValueError("bad ciphertext")
        return ciphertext[len("encrypted:"):]


class TestSecretSplit(unittest.TestCase):
    def test_recursively_splits_and_restores_secrets(self):
        payload = {
            "form": {"svnUsername": "dev", "svnPassword": "s3cr3t"},
            "server": {"private_key": "key-data"},
            "projects": [{"name": "demo", "token": "abc"}],
        }

        public, secrets = split_secrets(payload)

        self.assertEqual(public["form"]["svnPassword"], "[configured]")
        self.assertEqual(public["server"]["private_key"], "[configured]")
        self.assertNotIn("s3cr3t", repr(public))
        self.assertEqual(merge_secrets(public, secrets), payload)


class TestTaskStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.temp_dir.name), codec=FakeCodec())

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_request_id_is_idempotent_and_public_task_is_redacted(self):
        payload = {
            "projects": [{"name": "demo", "branch": "main"}],
            "config": {"form": {"svnPassword": "secret-value"}},
        }

        first, created = self.store.create_task("req-1", "run", "alice", payload)
        second, created_again = self.store.create_task("req-1", "run", "alice", payload)

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first["taskId"], second["taskId"])
        self.assertNotIn("secret-value", repr(self.store.get_task(first["taskId"])))
        restored = self.store.get_execution_payload(first["taskId"])
        self.assertEqual(restored["config"]["form"]["svnPassword"], "secret-value")

    def test_events_use_per_task_monotonic_sequence(self):
        task, _ = self.store.create_task("req-events", "run", "alice", {})
        task_id = task["taskId"]

        first = self.store.append_event(task_id, "status", {"status": "queued"})
        second = self.store.append_event(task_id, "log", {"message": "ready"})

        self.assertEqual(first["seq"], 1)
        self.assertEqual(second["seq"], 2)
        self.assertEqual([event["seq"] for event in self.store.list_events(task_id, after=1)], [2])

    def test_event_and_error_text_redact_persisted_secret_values(self):
        task, _ = self.store.create_task(
            "req-redact", "run", "alice", {"serverPassword": "top-secret"}
        )
        task_id = task["taskId"]
        event = self.store.append_event(
            task_id, "log", {"message": "command contained top-secret"}
        )
        self.store.set_status(task_id, "failed", error="failed with top-secret")

        self.assertNotIn("top-secret", repr(event))
        self.assertNotIn("top-secret", repr(self.store.get_task(task_id)))
        self.assertNotIn(
            "top-secret", (self.store.log_dir / f"{task_id}.ndjson").read_text("utf-8")
        )

    def test_restart_interrupts_active_tasks_and_keeps_fifo_queue(self):
        first, _ = self.store.create_task("req-a", "run", "alice", {})
        second, _ = self.store.create_task("req-b", "run", "bob", {})
        self.store.set_status(first["taskId"], "running")

        self.store.recover_after_restart()

        self.assertEqual(self.store.get_task(first["taskId"])["status"], "interrupted")
        queued = self.store.list_queued_ids()
        self.assertEqual(queued, [second["taskId"]])


if __name__ == "__main__":
    unittest.main()

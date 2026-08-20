# -*- coding: utf-8 -*-
"""Contract tests for persistent tasks, replay, origin checks, and downloads."""

import asyncio
import json
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import sys

from aiohttp import WSMsgType
from aiohttp.test_utils import AioHTTPTestCase

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.app import create_app
from server.config_service import WebConfigService
from server.secrets import SecretCodec
from server.task_manager import TaskManager
from server.task_store import TaskStore
from server.workspace import WorkspaceManager


class FakeCodec(SecretCodec):
    def encrypt(self, plaintext):
        return "enc:" + plaintext

    def decrypt(self, ciphertext):
        return ciphertext[4:]


class ImmediateRunner:
    async def stream_run(self, command_name, payload, event_callback, exit_callback, task_id):
        await event_callback({"type": "log", "message": "done"})
        await event_callback({"type": "result", "success": True, "projects": []})
        await exit_callback(0)
        return 0

    async def stop_run(self, task_id):
        return True


class TestWebServerAPI(AioHTTPTestCase):
    profile_id = "a" * 32

    @property
    def profile_headers(self):
        return {"Cookie": f"zbuild_profile={self.profile_id}"}

    async def get_application(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.store = TaskStore(root, codec=FakeCodec())
        self.workspace = WorkspaceManager(root, {})
        self.manager = TaskManager(self.store, ImmediateRunner(), self.workspace)
        self.config = WebConfigService(root / "config.json", codec=FakeCodec())
        return create_app(
            data_dir=root, task_store=self.store, task_manager=self.manager,
            workspace=self.workspace, config_service=self.config,
        )

    async def asyncTearDown(self):
        await super().asyncTearDown()
        self.store.close()
        self.temp_dir.cleanup()

    async def test_health_and_cross_origin_rejection(self):
        response = await self.client.get("/api/health")
        self.assertEqual(response.status, 200)
        rejected = await self.client.get(
            "/api/health", headers={"Origin": "https://evil.example"}
        )
        self.assertEqual(rejected.status, 403)
        self.assertEqual((await rejected.json())["error"]["code"], "origin_rejected")

    async def test_svn_list_uses_stored_password_when_browser_sends_configured_marker(self):
        self.config.save({"svn_root": "https://svn.example/root"}, "0")
        self.app["profile_store"].save(self.profile_id, {
            "svn_credentials": {"username": "svn-user", "password": "svn-secret"},
        }, "0")
        with patch("server.app.runner_service.execute_command", new_callable=AsyncMock) as execute:
            execute.return_value = {
                "success": True,
                "entries": [{"name": "医院 A", "kind": "dir"}],
            }
            response = await self.client.post("/api/svn/list", json={
                "svn": "svn",
                "url": "https://svn.example/root",
                "username": "svn-user",
                "password": "[configured]",
            }, headers=self.profile_headers)

        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), ["医院 A"])
        payload = execute.await_args.args[1]
        self.assertEqual(payload["username"], "svn-user")
        self.assertEqual(payload["password"], "svn-secret")

    async def test_svn_list_returns_runner_failure_without_multiline_http_error(self):
        self.config.save({"svn_root": "https://svn.example/root"}, "0")
        with patch("server.app.runner_service.execute_command", new_callable=AsyncMock) as execute:
            execute.return_value = {
                "success": False,
                "error": "Authentication failed\nTry again",
            }
            response = await self.client.post("/api/svn/list", json={"url": "https://svn.example/root"})

        self.assertEqual(response.status, 502)
        error = (await response.json())["error"]
        self.assertEqual(error["code"], "http_error")
        self.assertEqual(error["message"], "Authentication failed Try again")

    async def test_svn_list_rejects_unconfigured_repository_url(self):
        self.config.save({"svn_root": "https://svn.example/root"}, "0")
        response = await self.client.post("/api/svn/list", json={
            "url": "https://other.example/repository",
        }, headers=self.profile_headers)
        self.assertEqual(response.status, 400)

    async def test_config_save_keeps_server_paths_but_persists_profile_svn_credentials(self):
        self.config.save({
            "root_path": r"D:\server-workspace",
            "svn_root": "https://svn.example/root",
        }, "0")
        initial = await self.client.get("/api/config", headers=self.profile_headers)
        revision = (await initial.json())["revision"]
        response = await self.client.put("/api/config", json={
            "revision": revision,
            "config": {
                "rootPath": r"D:\not-allowed",
                "svnRootUrl": "https://other.example/repository",
                "selectedProjects": ["frontend"],
                "artifactPaths": ["custom-dist", "release-output"],
                "form": {"svnUsername": "alice", "svnPassword": "secret"},
            },
        }, headers=self.profile_headers)
        self.assertEqual(response.status, 200)
        current = await response.json()
        self.assertEqual(current["config"]["rootPath"], r"D:\server-workspace")
        self.assertEqual(current["config"]["svnRootUrl"], "https://svn.example/root")
        self.assertEqual(current["config"]["artifactPaths"], ["custom-dist", "release-output"])
        self.assertEqual(current["config"]["form"]["svnUsername"], "alice")
        self.assertEqual(current["config"]["form"]["svnPassword"], "[configured]")

    async def test_task_contract_and_event_replay(self):
        response = await self.client.post("/api/tasks", json={
            "requestId": "api-1", "type": "order-deploy-run", "submitter": "alice",
            "payload": {"items": []},
        }, headers=self.profile_headers)
        self.assertEqual(response.status, 202)
        task = await response.json()
        self.assertRegex(task["taskId"], r"^[0-9a-f]{32}$")

        for _ in range(100):
            detail_response = await self.client.get(
                f"/api/tasks/{task['taskId']}", headers=self.profile_headers
            )
            detail = await detail_response.json()
            if detail["status"] == "success":
                break
            await asyncio.sleep(0.01)
        self.assertEqual(detail["status"], "success")

        events_response = await self.client.get(
            f"/api/tasks/{task['taskId']}/events?after=1"
        , headers=self.profile_headers)
        events = await events_response.json()
        self.assertTrue(events)
        self.assertTrue(all(item["seq"] > 1 for item in events))

        ws = await self.client.ws_connect("/api/ws/tasks", headers=self.profile_headers)
        await ws.send_json({"action": "subscribe", "taskId": task["taskId"], "after": 0})
        message = await ws.receive(timeout=1)
        self.assertEqual(message.type, WSMsgType.TEXT)
        self.assertEqual(json.loads(message.data)["type"], "task_event")
        await ws.close()

    async def test_binary_artifact_download_and_path_scoping(self):
        task, _ = self.store.create_task("download-1", "run", "bob", {}, self.profile_id)
        artifact_dir = self.workspace.artifact_root / task["taskId"]
        artifact_dir.mkdir(parents=True)
        artifact = artifact_dir / "sample.bin"
        artifact.write_bytes(b"\x00\xffzbuild")
        saved = self.store.add_artifact(
            task["taskId"], artifact.name, artifact, "application/octet-stream"
        )
        response = await self.client.get(
            f"/api/tasks/{task['taskId']}/artifacts/{saved['artifactId']}"
        , headers=self.profile_headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.read(), b"\x00\xffzbuild")
        missing = await self.client.get(
            f"/api/tasks/{task['taskId']}/artifacts/not-real"
        , headers=self.profile_headers)
        self.assertEqual(missing.status, 404)

    async def test_task_detail_never_exposes_internal_payload_or_paths(self):
        task, _ = self.store.create_task(
            "detail-redaction-1",
            "run",
            "alice",
            {
                "config": {"svnPassword": "plain-secret"},
                "_trusted_projects": {"app": r"D:\secret\base-repo"},
            }, self.profile_id,
        )
        self.store.set_status(
            task["taskId"],
            "failed",
            error=r"Build failed in D:\secret\base-repo\src",
            result={
                "projects": [{
                    "name": "app",
                    "baseRepo": r"D:\secret\base-repo",
                    "worktree": r"D:\secret\worktrees\task\app",
                    "artifact": {
                        "path": r"D:\secret\artifacts\task\app.zip",
                        "sha256": "abc123",
                    },
                    "config": {"password": "plain-secret"},
                }],
                "targetUrl": r"D:\secret\upload-target",
            },
        )

        response = await self.client.get(
            f"/api/tasks/{task['taskId']}", headers=self.profile_headers
        )
        self.assertEqual(response.status, 200)
        detail = await response.json()
        serialized = json.dumps(detail, ensure_ascii=False)
        for private_value in (
            "payload", "config", "_trusted_projects", "baseRepo", "worktree",
            "plain-secret", r"D:\secret",
        ):
            self.assertNotIn(private_value, serialized)
        self.assertEqual(
            detail["result"]["projects"][0]["artifact"], {"sha256": "abc123"}
        )
        self.assertIn("[path]", detail["error"])

    async def test_tasks_are_not_visible_from_another_browser_profile(self):
        task, _ = self.store.create_task("private-task", "run", "alice", {}, self.profile_id)
        other = {"Cookie": "zbuild_profile=" + "b" * 32}
        response = await self.client.get(f"/api/tasks/{task['taskId']}", headers=other)
        self.assertEqual(response.status, 404)
        listed = await self.client.get("/api/tasks", headers=other)
        self.assertEqual(await listed.json(), [])


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Integration tests for detached per-task Git worktrees and artifacts."""

import asyncio
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.workspace import WorkspaceManager


def git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git is required")
class TestWorkspaceManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.remote = root / "remote.git"
        self.seed = root / "seed"
        self.base = root / "base"
        self.data = root / "data"
        git("init", "--bare", str(self.remote))
        git("init", "-b", "main", str(self.seed))
        git("config", "user.email", "test@example.com", cwd=self.seed)
        git("config", "user.name", "Test", cwd=self.seed)
        (self.seed / "README.md").write_text("demo", encoding="utf-8")
        git("add", "README.md", cwd=self.seed)
        git("commit", "-m", "initial", cwd=self.seed)
        git("remote", "add", "origin", str(self.remote), cwd=self.seed)
        git("push", "-u", "origin", "main", cwd=self.seed)
        git("clone", "--branch", "main", str(self.remote), str(self.base))
        self.manager = WorkspaceManager(self.data, {"demo": self.base})

    async def asyncTearDown(self):
        await self.manager.cleanup("task-a")
        await self.manager.cleanup("task-b")
        self.temp_dir.cleanup()

    async def test_same_branch_tasks_get_distinct_detached_worktrees(self):
        payload = {
            "projects": [{"name": "demo", "path": "C:/untrusted", "branch": "main"}],
            "auto_pull": True,
            "restore_branch": True,
        }

        (prepared_a, commits_a), (prepared_b, commits_b) = await asyncio.gather(
            self.manager.prepare("task-a", payload),
            self.manager.prepare("task-b", payload),
        )

        path_a = Path(prepared_a["projects"][0]["path"])
        path_b = Path(prepared_b["projects"][0]["path"])
        self.assertNotEqual(path_a, path_b)
        self.assertTrue((path_a / "README.md").is_file())
        self.assertTrue((path_b / "README.md").is_file())
        self.assertEqual(git("status", "--porcelain", cwd=self.base), "")
        self.assertEqual(git("branch", "--show-current", cwd=self.base), "main")
        self.assertEqual(commits_a[0]["sha"], commits_b[0]["sha"])
        self.assertTrue(prepared_a["isolated_workspace"])
        self.assertFalse(prepared_a["auto_pull"])
        self.assertFalse(prepared_a["restore_branch"])

    async def test_unknown_project_is_rejected_before_git_runs(self):
        with self.assertRaisesRegex(ValueError, "Unknown project"):
            await self.manager.prepare(
                "task-a", {"projects": [{"name": "other", "branch": "main"}]}
            )


if __name__ == "__main__":
    unittest.main()

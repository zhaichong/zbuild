# -*- coding: utf-8 -*-
"""GIT_EXECUTABLE must be applied so discover can list branches without PATH git."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tools.env_setup import apply_tools_env, _tool_path


class TestEnvSetup(unittest.TestCase):
    def test_tool_path_string_and_object(self):
        self.assertEqual(_tool_path({"git": "C:/git.exe"}, "git"), "C:/git.exe")
        self.assertEqual(
            _tool_path({"git": {"path": "C:/Program Files/Git/cmd/git.exe", "version": "2"}}, "git"),
            "C:/Program Files/Git/cmd/git.exe",
        )
        self.assertEqual(_tool_path({}, "git"), "")

    def test_apply_tools_env_sets_git_executable(self):
        # Use a fake path that exists for this test
        fake = Path(__file__).resolve()
        prev = os.environ.get("GIT_EXECUTABLE")
        try:
            apply_tools_env({"tools": {"git": str(fake)}})
            self.assertEqual(os.environ.get("GIT_EXECUTABLE"), str(fake))
        finally:
            if prev is None:
                os.environ.pop("GIT_EXECUTABLE", None)
            else:
                os.environ["GIT_EXECUTABLE"] = prev

    def test_discover_with_tools_without_path_git(self):
        """Regression: empty PATH git still returns current_branch via tools.git."""
        from tools.detect import find_tool
        from git.discover import discover_projects
        from tools.env_setup import apply_tools_env

        git = find_tool("git")
        if not git:
            self.skipTest("git not installed on this machine")

        root = Path(r"D:\build")
        if not root.is_dir():
            self.skipTest("D:\\build not present")

        # Clear GIT_EXECUTABLE and strip git from PATH for this process scope
        prev_git = os.environ.pop("GIT_EXECUTABLE", None)
        prev_path = os.environ.get("PATH", "")
        try:
            parts = [p for p in prev_path.split(os.pathsep) if "git" not in p.lower()]
            os.environ["PATH"] = os.pathsep.join(parts)

            # Without tools → empty branches
            from git.branches import read_current_branch

            empty = read_current_branch(root / "zhbf-fontend") if (root / "zhbf-fontend").is_dir() else ""
            # May still find git via other means; force safe_git path by unsetting after apply failure
            # Apply tools explicitly
            apply_tools_env({"tools": {"git": git}})
            self.assertEqual(os.environ.get("GIT_EXECUTABLE"), git)

            projects = discover_projects([str(root)])
            self.assertGreater(len(projects), 0)
            with_branch = [p for p in projects if p.current_branch]
            self.assertGreater(
                len(with_branch),
                0,
                "expected at least one project with current_branch after apply_tools_env",
            )
        finally:
            if prev_git is not None:
                os.environ["GIT_EXECUTABLE"] = prev_git
            else:
                os.environ.pop("GIT_EXECUTABLE", None)
            os.environ["PATH"] = prev_path


if __name__ == "__main__":
    unittest.main()

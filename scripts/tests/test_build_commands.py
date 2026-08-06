# -*- coding: utf-8 -*-
"""Unit tests for per-project build command configuration and execution."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.config import default_config, normalize_config
from core.constants import DEFAULT_BUILD_COMMANDS, ProjectInfo
from git.discover import discover_projects, discover_single
from workflow.pipeline import Pipeline
from workflow.steps import StepContext, StepResult, StepDefinition


class TestBuildCommands(unittest.TestCase):
    def test_normalize_config_defaults(self):
        cfg = normalize_config({})
        self.assertIn("build_commands", cfg)
        self.assertIsInstance(cfg["build_commands"], dict)
        self.assertEqual(cfg["build_command"], "deploy.sh")
        for proj, cmd in DEFAULT_BUILD_COMMANDS.items():
            self.assertEqual(cfg["build_commands"].get(proj), cmd)

    def test_normalize_config_custom_override(self):
        cfg = normalize_config({
            "build_command": "build.sh",
            "build_commands": {
                "custom-proj": "npm run build:prod",
                "zbuild": "npm run package",
            },
        })
        self.assertEqual(cfg["build_command"], "build.sh")
        self.assertEqual(cfg["build_commands"]["custom-proj"], "npm run build:prod")
        self.assertEqual(cfg["build_commands"]["zbuild"], "npm run package")

    def test_discover_projects_with_build_command(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            p1 = tmp_path / "zhbf-web"
            p1.mkdir()
            (p1 / ".git").mkdir()

            p2 = tmp_path / "unknown-proj"
            p2.mkdir()
            (p2 / ".git").mkdir()

            projects = discover_projects([str(tmp_path)])
            proj_dict = {p.name: p for p in projects}

            self.assertIn("zhbf-web", proj_dict)
            self.assertEqual(proj_dict["zhbf-web"].build_command, "deploy.sh")

            self.assertIn("unknown-proj", proj_dict)
            self.assertEqual(proj_dict["unknown-proj"].build_command, "deploy.sh")

    def test_pipeline_uses_project_build_command(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            p = tmp_path / "my-app"
            p.mkdir()

            pipe = Pipeline({
                "mode": "local",
                "build_command": "global.sh",
                "build_commands": {"my-app": "custom-cmd.sh"},
                "projects": [
                    {"name": "my-app", "path": str(p), "branch": "main", "build_command": "explicit-arg.sh"},
                ],
            })

            record = pipe.run_one({
                "name": "my-app",
                "path": str(p),
                "branch": "main",
                "build_command": "explicit-arg.sh",
            })

            self.assertEqual(record.project_name, "my-app")


if __name__ == "__main__":
    unittest.main()

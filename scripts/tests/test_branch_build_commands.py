# -*- coding: utf-8 -*-
"""Unit tests for per-branch build command configuration and execution."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.config import default_config, normalize_config
from git.build_cmd import resolve_branch_build_command


class TestBranchBuildCommands(unittest.TestCase):
    def test_normalize_config_with_branch_commands(self):
        cfg = normalize_config({
            "build_command": "deploy.sh",
            "build_commands": {
                "yarward-web-frontend": "npm run build:default",
            },
            "branch_build_commands": {
                "yarward-web-frontend": {
                    "master": "npm run build:prod",
                    "v2.0-vite": "pnpm run build",
                    "feat/*": "npm run build:test",
                }
            }
        })
        self.assertIn("branch_build_commands", cfg)
        self.assertIn("yarward-web-frontend", cfg["branch_build_commands"])
        self.assertEqual(cfg["branch_build_commands"]["yarward-web-frontend"]["master"], "npm run build:prod")
        self.assertEqual(cfg["branch_build_commands"]["yarward-web-frontend"]["v2.0-vite"], "pnpm run build")
        self.assertEqual(cfg["branch_build_commands"]["yarward-web-frontend"]["feat/*"], "npm run build:test")

    def test_resolve_exact_branch_command(self):
        cfg = {
            "build_command": "deploy.sh",
            "build_commands": {"yarward-web-frontend": "npm run build:default"},
            "branch_build_commands": {
                "yarward-web-frontend": {
                    "master": "npm run build:prod",
                    "dev": "npm run build:dev",
                }
            }
        }
        cmd = resolve_branch_build_command(cfg, "yarward-web-frontend", "master")
        self.assertEqual(cmd, "npm run build:prod")

        cmd_dev = resolve_branch_build_command(cfg, "yarward-web-frontend", "dev")
        self.assertEqual(cmd_dev, "npm run build:dev")

    def test_resolve_wildcard_branch_command(self):
        cfg = {
            "build_command": "deploy.sh",
            "build_commands": {"yarward-web-frontend": "npm run build:default"},
            "branch_build_commands": {
                "yarward-web-frontend": {
                    "release/*": "npm run build:release",
                    "feat/*": "npm run build:test",
                }
            }
        }
        cmd_rel = resolve_branch_build_command(cfg, "yarward-web-frontend", "release/2026.1")
        self.assertEqual(cmd_rel, "npm run build:release")

        cmd_feat = resolve_branch_build_command(cfg, "yarward-web-frontend", "feat/login")
        self.assertEqual(cmd_feat, "npm run build:test")

    def test_fallback_to_project_and_global_command(self):
        cfg = {
            "build_command": "global.sh",
            "build_commands": {"yarward-web-frontend": "proj-default.sh"},
            "branch_build_commands": {
                "yarward-web-frontend": {
                    "master": "npm run build:prod"
                }
            }
        }
        # Other branch in same project -> fallback to project default
        cmd_other = resolve_branch_build_command(cfg, "yarward-web-frontend", "other-branch")
        self.assertEqual(cmd_other, "proj-default.sh")

        # Unknown project -> fallback to global default
        cmd_unknown = resolve_branch_build_command(cfg, "unknown-proj", "master")
        self.assertEqual(cmd_unknown, "global.sh")


if __name__ == "__main__":
    unittest.main()

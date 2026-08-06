# -*- coding: utf-8 -*-
"""Regression: Node 14 must never run a foreign (Volta/global) npm 10+ CLI."""

import os
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from git.deps import _node_env
from tools.bundled import (
    bundled_node,
    bundled_npm,
    find_node14_dir,
    node_shim_dir,
    npm_isolated_prefix_dir,
    _node14_cli_js,
)
from tools.exec import run_process


class TestNodeShims(unittest.TestCase):
    def test_npm_shim_invokes_local_cli_js(self):
        node = bundled_node()
        if not node:
            self.skipTest("Node 14 not available")

        npm_cli = _node14_cli_js("npm")
        self.assertTrue(npm_cli, "expected Node 14 npm-cli.js next to runtime/Volta node")

        shim_dir = node_shim_dir()
        npm_cmd = (shim_dir / "npm.cmd").read_text(encoding="utf-8")
        npm_sh = (shim_dir / "npm").read_text(encoding="utf-8")

        # Direct node + local cli — never shell out to stock npm.cmd
        # (that wrapper re-resolves global prefix onto foreign npm 10+).
        self.assertIn("npm-cli.js", npm_cmd)
        self.assertIn(Path(node).name, npm_cmd)
        self.assertNotIn("\\npm.cmd", npm_cmd.replace("/", "\\"))
        self.assertIn("npm-cli.js", npm_sh)
        # LF shebang only (no CRLF shebang that bash would ignore)
        self.assertTrue(npm_sh.startswith("#!/bin/sh\n"), repr(npm_sh[:20]))

    def test_node_env_isolates_npm_prefix(self):
        env = _node_env()
        prefix = str(npm_isolated_prefix_dir())
        self.assertEqual(env.get("npm_config_prefix"), prefix)
        self.assertEqual(env.get("NPM_CONFIG_PREFIX"), prefix)
        shim = str(node_shim_dir())
        self.assertTrue(env["PATH"].startswith(shim) or env["PATH"].lower().startswith(shim.lower()))

    def test_npm_version_under_node14_is_v6_family(self):
        """Live check: npm must report 6.x when run under our env (not 10.x)."""
        node = bundled_node()
        npm_cli = _node14_cli_js("npm")
        if not node or not npm_cli:
            self.skipTest("Node 14 / npm-cli.js not available")

        env = _node_env()
        # Direct safe invocation
        r = run_process([node, npm_cli, "--version"], env=env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        ver = r.stdout.strip()
        self.assertTrue(ver.startswith("6."), f"expected npm 6.x, got {ver!r}")

        # Shim path used by package_manager_executable / PATH
        npm = bundled_npm()
        self.assertTrue(npm)
        r2 = run_process([npm, "--version"], env=env, timeout=30)
        self.assertEqual(r2.returncode, 0, r2.stderr or r2.stdout)
        ver2 = r2.stdout.strip()
        self.assertTrue(ver2.startswith("6."), f"shim npm expected 6.x, got {ver2!r}")

        # Stock npm.cmd under isolated prefix must also stay on 6.x
        node14 = find_node14_dir()
        if node14 and (node14 / "npm.cmd").is_file():
            r3 = run_process([str(node14 / "npm.cmd"), "--version"], env=env, timeout=30)
            self.assertEqual(r3.returncode, 0, r3.stderr or r3.stdout)
            ver3 = r3.stdout.strip()
            self.assertTrue(
                ver3.startswith("6."),
                f"stock npm.cmd under isolated prefix expected 6.x, got {ver3!r}",
            )


if __name__ == "__main__":
    unittest.main()

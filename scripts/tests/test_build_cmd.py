# -*- coding: utf-8 -*-

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.errors import BuildError
from git.build_cmd import validate_build_command, resolve_run_argv


class TestBuildCmdValidation(unittest.TestCase):
    def test_allows_deploy_sh(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "deploy.sh").write_text("#!/bin/bash\necho ok\n", encoding="utf-8")
            argv = validate_build_command(project, "deploy.sh")
            self.assertEqual(argv[0], "bash")
            self.assertEqual(argv[1], "deploy.sh")

    def test_allows_npm_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            argv = validate_build_command(temp_dir, "npm run build:prod")
            self.assertEqual(argv, ["npm", "run", "build:prod"])

    def test_rejects_shell_metacharacters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(BuildError):
                validate_build_command(temp_dir, "deploy.sh; rm -rf /")

    def test_rejects_bash_c(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(BuildError):
                validate_build_command(temp_dir, 'bash -c "echo pwned"')

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(BuildError):
                validate_build_command(temp_dir, "../outside.sh")

    def test_rejects_unknown_runner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(BuildError):
                validate_build_command(temp_dir, "python -c pass")

    def test_resolve_run_argv_substitutes_bash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "deploy.sh").write_text("exit 0\n", encoding="utf-8")
            argv, cmd = resolve_run_argv(project, "deploy.sh", bash_exe=r"C:\Git\bin\bash.exe")
            self.assertEqual(argv[0], r"C:\Git\bin\bash.exe")
            self.assertEqual(cmd, "deploy.sh")

    def test_auto_detects_package_json_build_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "package.json").write_text('{"scripts": {"build:prod": "vite build"}}', encoding="utf-8")
            # Without deploy.sh present, requesting deploy.sh should auto-detect package.json
            argv = validate_build_command(project, "deploy.sh")
            self.assertEqual(argv, ["npm", "run", "build:prod"])

    def test_auto_detects_pnpm_lock_uses_npm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "package.json").write_text('{"scripts": {"build": "vue-tsc && vite build"}}', encoding="utf-8")
            (project / "pnpm-lock.yaml").write_text("lockfileVersion: 5.4", encoding="utf-8")
            argv = validate_build_command(project, "deploy.sh")
            self.assertEqual(argv, ["npm", "run", "build"])


if __name__ == "__main__":
    unittest.main()

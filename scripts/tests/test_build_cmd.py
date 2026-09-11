# -*- coding: utf-8 -*-

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.errors import BuildError
from git.build_cmd import (
    is_micro_frontend_context,
    parse_branch_version,
    resolve_branch_build_command,
    resolve_project_node_version,
    resolve_run_argv,
    validate_build_command,
)


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


class TestWebFrontendMicroCommand(unittest.TestCase):
    def setUp(self):
        self.config = {
            "build_command": "deploy.sh",
            "build_commands": {
                "yarward-web-frontend": "deploy.sh",
                "yarward-ntv-frontend": "deploy.sh",
            },
            "branch_build_commands": {
                "yarward-web-frontend": {
                    "3.5.0*": "deploy.sh",
                    "3.4.4_台州市中心医院": "deploy.sh",
                },
            },
        }

    def test_parse_branch_version(self):
        self.assertEqual(parse_branch_version("3.4.4_台州市中心医院"), (3, 4, 4))
        self.assertEqual(parse_branch_version("3.5.0"), (3, 5, 0))
        self.assertEqual(parse_branch_version("3.4"), (3, 4, 0))
        self.assertIsNone(parse_branch_version("main"))
        self.assertIsNone(parse_branch_version("master"))

    def test_web_frontend_uses_micro_from_344(self):
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.4.4_台州市中心医院"),
            "deploy-micro.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.4.4"),
            "deploy-micro.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.5.0"),
            "deploy-micro.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.10.0_某医院"),
            "deploy-micro.sh",
        )

    def test_web_frontend_below_344_keeps_default(self):
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.4.2_复旦大学附属华山医院宝山"),
            "deploy.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "3.1.3_上海市第一人民医院松江南院"),
            "deploy.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-web-frontend", "main"),
            "deploy.sh",
        )

    def test_other_projects_ignore_web_frontend_version_rule(self):
        self.assertEqual(
            resolve_branch_build_command(self.config, "yarward-ntv-frontend", "3.5.0"),
            "deploy.sh",
        )
        self.assertEqual(
            resolve_branch_build_command(self.config, "zhbf-bedhead-frontend", "3.4.4_台州市中心医院"),
            "deploy.sh",
        )

    def test_micro_context_and_node_version(self):
        self.assertTrue(is_micro_frontend_context(branch="3.4.4_台州市中心医院"))
        self.assertFalse(is_micro_frontend_context(branch="3.4.2_复旦"))
        self.assertEqual(
            resolve_project_node_version("yarward-micro-menu", branch="3.4.4_台州市中心医院"),
            "22",
        )
        self.assertEqual(
            resolve_project_node_version("yarward-web-frontend", branch="3.4.4_台州市中心医院"),
            "14",
        )
        self.assertEqual(
            resolve_project_node_version("yarward-micro-menu", branch="3.4.2_复旦"),
            "14",
        )


if __name__ == "__main__":
    unittest.main()

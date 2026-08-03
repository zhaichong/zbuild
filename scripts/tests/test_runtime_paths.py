# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


class TestRuntimePaths(unittest.TestCase):
    def test_data_paths_follow_zbuild_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["ZBUILD_DATA_DIR"] = temp_dir
            code = (
                "from core.constants import CONFIG_PATH, HISTORY_DIR, TEMPLATES_DIR; "
                "print(CONFIG_PATH); print(HISTORY_DIR); print(TEMPLATES_DIR)"
            )
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=SCRIPTS_DIR,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            paths = [Path(line) for line in result.stdout.splitlines()]
            data_dir = Path(temp_dir).resolve()
            self.assertEqual(paths[0], data_dir / "tool-config.json")
            self.assertEqual(paths[1], data_dir / "history")
            self.assertEqual(paths[2], data_dir / "templates")

    def test_development_paths_keep_existing_references_layout(self):
        env = os.environ.copy()
        env.pop("ZBUILD_DATA_DIR", None)
        code = "from core.constants import CONFIG_PATH; print(CONFIG_PATH)"
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=SCRIPTS_DIR,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), SCRIPTS_DIR.parent / "references" / "tool-config.json")


if __name__ == "__main__":
    unittest.main()

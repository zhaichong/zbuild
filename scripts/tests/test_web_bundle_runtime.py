# -*- coding: utf-8 -*-
"""Regression checks for the zero-install Web service runtime."""

import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_PYTHON = PROJECT_ROOT / "runtime" / "python" / "python.exe"


class TestWebBundleRuntime(unittest.TestCase):
    def test_bundled_python_can_import_web_server_dependencies(self):
        """A target machine must start the Web service without system Python."""
        self.assertTrue(BUNDLED_PYTHON.is_file(), "缺少 runtime/python/python.exe")
        result = subprocess.run(
            [str(BUNDLED_PYTHON), "-c", "import aiohttp; print(aiohttp.__version__)"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

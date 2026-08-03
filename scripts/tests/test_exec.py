# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tools.exec import run_process


class TestProcessLogging(unittest.TestCase):
    def test_password_argument_is_redacted_from_debug_log(self):
        with self.assertLogs("tools.exec", level="DEBUG") as captured:
            result = run_process(
                [sys.executable, "-c", "pass", "--password", "super-secret"]
            )

        self.assertEqual(result.returncode, 0)
        log_text = "\n".join(captured.output)
        self.assertNotIn("super-secret", log_text)
        self.assertIn("***", log_text)


if __name__ == "__main__":
    unittest.main()

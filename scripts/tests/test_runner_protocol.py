# -*- coding: utf-8 -*-

import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestRunnerProtocol(unittest.TestCase):
    def test_reads_utf8_json_from_subprocess_stdin(self):
        payload = {"url": "https://svn.example/svn/智慧病房特殊订单"}
        script = (
            "import json, sys; sys.path.insert(0, 'scripts'); "
            "from runner.protocol import read_stdin_json; "
            "print(json.dumps(read_stdin_json(), ensure_ascii=True))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_ROOT,
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            check=True,
        )

        self.assertEqual(json.loads(result.stdout.decode("utf-8")), payload)


if __name__ == "__main__":
    unittest.main()

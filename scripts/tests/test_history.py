# -*- coding: utf-8 -*-

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.history import HistoryStore
from core.models import ExecutionRecord


class TestHistorySecrets(unittest.TestCase):
    def test_create_does_not_persist_passwords(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = HistoryStore(Path(temp_dir))
            record = ExecutionRecord(
                run_id="secret-test",
                mode="server",
                config_snapshot={
                    "hospital_name": "test-hospital",
                    "svn_credentials": {"username": "svn-user", "password": "svn-secret"},
                    "server": {"username": "ssh-user", "password": "ssh-secret"},
                },
            )

            store.create(record)

            record_text = (Path(temp_dir) / "secret-test.json").read_text(encoding="utf-8")
            index_text = (Path(temp_dir) / "index.json").read_text(encoding="utf-8")
            self.assertNotIn("svn-secret", record_text)
            self.assertNotIn("ssh-secret", record_text)
            self.assertNotIn("svn-secret", index_text)
            self.assertNotIn("ssh-secret", index_text)
            self.assertEqual(json.loads(record_text)["config_snapshot"]["hospital_name"], "test-hospital")


if __name__ == "__main__":
    unittest.main()

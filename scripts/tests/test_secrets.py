# -*- coding: utf-8 -*-

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.secrets import without_secrets
from core.templates import TemplateStore
from core.models import TaskTemplate


class TestWithoutSecrets(unittest.TestCase):
    def test_strips_nested_passwords(self):
        data = {
            "hospital_name": "demo",
            "svn_credentials": {"username": "u", "password": "p1"},
            "server": {"host": "h", "password": "p2", "token": "t1"},
            "list": [{"api_key": "k", "name": "x"}],
        }
        cleaned = without_secrets(data)
        text = json.dumps(cleaned)
        self.assertNotIn("p1", text)
        self.assertNotIn("p2", text)
        self.assertNotIn("t1", text)
        self.assertNotIn("k", text)
        self.assertEqual(cleaned["hospital_name"], "demo")
        self.assertEqual(cleaned["svn_credentials"]["username"], "u")
        self.assertEqual(cleaned["list"][0]["name"], "x")


class TestTemplateStoreSecrets(unittest.TestCase):
    def test_create_and_update_strip_passwords(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TemplateStore(Path(temp_dir))
            tpl = TaskTemplate(
                template_id="tpl1",
                name="demo",
                mode="svn",
                config={
                    "svn_credentials": {"username": "u", "password": "secret-pass"},
                    "hospital_name": "h1",
                },
            )
            store.create(tpl)
            raw = (Path(temp_dir) / "tpl1.json").read_text(encoding="utf-8")
            self.assertNotIn("secret-pass", raw)
            self.assertIn("hospital_name", raw)

            loaded = store.get("tpl1")
            self.assertIsNotNone(loaded)
            self.assertNotIn("password", loaded.config.get("svn_credentials", {}))

            loaded.config = {
                "svn_credentials": {"username": "u2", "password": "another-secret"},
                "hospital_name": "h2",
            }
            store.update(loaded)
            raw2 = (Path(temp_dir) / "tpl1.json").read_text(encoding="utf-8")
            self.assertNotIn("another-secret", raw2)
            self.assertIn("h2", raw2)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.profile_store import ProfileConflict, ProfileStore
from server.secrets import SecretCodec


class FakeCodec(SecretCodec):
    def encrypt(self, plaintext): return "enc:" + plaintext
    def decrypt(self, ciphertext): return ciphertext[4:]


class TestProfileStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = ProfileStore(Path(self.temp_dir.name), codec=FakeCodec())

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_profile_secrets_are_encrypted_and_isolated(self):
        profile_a = self.store.save("a" * 32, {
            "selected_projects": ["frontend"],
            "svn_credentials": {"username": "alice", "password": "alice-secret"},
        }, "0")
        self.store.save("b" * 32, {
            "svn_credentials": {"username": "bob", "password": "bob-secret"},
        }, "0")

        self.assertTrue(profile_a["secretStatus"]["svnPassword"])
        self.assertNotIn("alice-secret", repr(profile_a))
        self.assertEqual(
            self.store.get_execution_config("a" * 32)["svn_credentials"]["password"],
            "alice-secret",
        )
        self.assertEqual(
            self.store.get_execution_config("b" * 32)["svn_credentials"]["username"], "bob",
        )

    def test_configured_marker_keeps_existing_password(self):
        first = self.store.save("a" * 32, {
            "svn_credentials": {"username": "alice", "password": "secret"},
            "server": {"host": "192.168.1.100", "username": "admin", "password": "server-secret"},
        }, "0")
        self.assertTrue(first["secretStatus"]["serverPassword"])
        self.store.save("a" * 32, {
            "svn_credentials": {"username": "alice-2", "password": "[configured]"},
            "server": {"host": "192.168.1.100", "username": "admin", "password": "[configured]"},
        }, first["revision"])
        current = self.store.get_execution_config("a" * 32)
        self.assertEqual(current["svn_credentials"], {"username": "alice-2", "password": "secret"})
        self.assertEqual(current["server"]["password"], "server-secret")

    def test_save_rejects_stale_revision(self):
        self.store.save("a" * 32, {}, "0")
        with self.assertRaises(ProfileConflict):
            self.store.save("a" * 32, {}, "0")

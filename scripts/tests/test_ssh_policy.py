# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from uploaders import ssh_policy


class _FakeClient:
    def __init__(self):
        self.policy = None
        self._keys = types.SimpleNamespace(add=lambda *a, **k: None)

    def load_system_host_keys(self):
        return None

    def load_host_keys(self, _path):
        return None

    def get_host_keys(self):
        return self._keys

    def save_host_keys(self, path):
        Path(path).write_text("host key\n", encoding="utf-8")

    def set_missing_host_key_policy(self, policy):
        self.policy = policy


class TestSshPolicy(unittest.TestCase):
    def test_strict_mode_uses_reject_policy(self):
        client = _FakeClient()
        reject = object()
        fake_paramiko = types.SimpleNamespace(
            SSHClient=lambda: client,
            RejectPolicy=lambda: reject,
            MissingHostKeyPolicy=object,
        )
        with patch.dict(os.environ, {"ZBUILD_SSH_STRICT": "1"}):
            out = ssh_policy.open_ssh_client(fake_paramiko)
        self.assertIs(out, client)
        self.assertIs(client.policy, reject)

    def test_default_tofu_persists_host_key(self):
        client = _FakeClient()
        fake_paramiko = types.SimpleNamespace(
            SSHClient=lambda: client,
            RejectPolicy=lambda: object(),
            MissingHostKeyPolicy=object,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"ZBUILD_SSH_STRICT": "0", "ZBUILD_DATA_DIR": temp_dir}):
                # Reload DATA_DIR used by known_hosts_path — patch the function return
                kh = Path(temp_dir) / "ssh_known_hosts"
                with patch.object(ssh_policy, "known_hosts_path", return_value=kh):
                    out = ssh_policy.open_ssh_client(fake_paramiko)
                    self.assertIs(out, client)
                    self.assertIsNotNone(client.policy)
                    key = types.SimpleNamespace(get_name=lambda: "ssh-rsa")
                    client.policy.missing_host_key(client, "host.example", key)
                    self.assertTrue(kh.exists())


if __name__ == "__main__":
    unittest.main()

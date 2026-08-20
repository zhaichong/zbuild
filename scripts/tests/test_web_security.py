# -*- coding: utf-8 -*-
"""Security boundary tests for Web origins, proxy URLs, and secure config."""

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.config_service import ConfigConflict, WebConfigService
from server.security import assert_origin_allowed, resolve_safe_proxy_target
from server.secrets import SecretCodec


class FakeCodec(SecretCodec):
    def encrypt(self, plaintext: str) -> str:
        return "cipher:" + plaintext[::-1]

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext[len("cipher:"):][::-1]


class TestOriginPolicy(unittest.TestCase):
    def test_same_origin_and_explicit_dev_origin_only(self):
        assert_origin_allowed("http://build.local:8000", "http", "build.local:8000", set())
        assert_origin_allowed(
            "http://localhost:5173", "http", "build.local:8000",
            {"http://localhost:5173"},
        )
        with self.assertRaises(ValueError):
            assert_origin_allowed("https://evil.example", "http", "build.local:8000", set())


class TestProxyPolicy(unittest.TestCase):
    def test_private_target_allowed_but_metadata_loopback_and_public_rejected(self):
        target = resolve_safe_proxy_target(
            "http://hospital.internal/api", "GET", set(),
            resolver=lambda _host: ["10.1.2.3"],
        )
        self.assertEqual(target.addresses, ("10.1.2.3",))
        for address in ("127.0.0.1", "169.254.169.254", "8.8.8.8"):
            with self.assertRaises(ValueError, msg=address):
                resolve_safe_proxy_target(
                    f"http://{address}/", "GET", set(), resolver=lambda _host: [address]
                )

    def test_method_scheme_and_dns_rebinding_shape_are_rejected(self):
        with self.assertRaises(ValueError):
            resolve_safe_proxy_target("file:///etc/passwd", "GET", set())
        with self.assertRaises(ValueError):
            resolve_safe_proxy_target("http://10.1.2.3", "DELETE", set())
        with self.assertRaises(ValueError):
            resolve_safe_proxy_target(
                "https://mixed.internal", "POST", set(),
                resolver=lambda _host: ["10.1.2.3", "8.8.8.8"],
            )


class TestWebConfigService(unittest.TestCase):
    def test_passwords_are_ciphertext_at_rest_and_never_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            service = WebConfigService(path, codec=FakeCodec())
            initial = service.get_public()
            saved = service.save({
                "svn_credentials": {"username": "dev", "password": "svn-secret"},
                "server": {"host": "10.0.0.2", "password": "ssh-secret"},
            }, initial["revision"])

            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("svn-secret", raw)
            self.assertNotIn("ssh-secret", raw)
            self.assertEqual(saved["config"]["svn_credentials"]["password"], "")
            self.assertTrue(saved["secretStatus"]["svnPassword"])
            self.assertEqual(
                service.get_execution_config()["server"]["password"], "ssh-secret"
            )

    def test_revision_conflict_and_empty_secret_preserves_existing_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = WebConfigService(Path(temp_dir) / "config.json", codec=FakeCodec())
            first = service.get_public()
            saved = service.save(
                {"svn_credentials": {"password": "keep-me"}}, first["revision"]
            )
            service.save(
                {"svn_credentials": {"password": ""}}, saved["revision"]
            )
            self.assertEqual(
                service.get_execution_config()["svn_credentials"]["password"], "keep-me"
            )
            with self.assertRaises(ConfigConflict):
                service.save({}, first["revision"])


if __name__ == "__main__":
    unittest.main()

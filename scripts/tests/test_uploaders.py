# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import io
import sys
import tarfile
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from uploaders.base import UploadResult, as_log_fn
from uploaders.server import ServerUploader
from uploaders.svn import SvnUploader, join_svn_url, upload_artifact, _is_same_project_artifact


class _FakeStream:
    def __init__(self):
        self.channel = types.SimpleNamespace(recv_exit_status=lambda: 0)

    def read(self):
        return b""


class _FakeSftp:
    def __init__(self):
        self.uploads = []

    def stat(self, _path):
        return True

    def mkdir(self, _path):
        return None

    def put(self, local, remote):
        self.uploads.append((local, remote))

    def close(self):
        return None


class _FakeSsh:
    def __init__(self):
        self.sftp = _FakeSftp()
        self.commands = []

    def set_missing_host_key_policy(self, _policy):
        return None

    def connect(self, **_kwargs):
        return None

    def open_sftp(self):
        return self.sftp

    def exec_command(self, command):
        self.commands.append(command)
        stream = _FakeStream()
        return None, stream, stream

    def close(self):
        return None


class TestServerUploader(unittest.TestCase):
    def test_upload_uses_project_specific_server_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "project.tar.gz"
            with tarfile.open(artifact, "w:gz") as archive:
                info = tarfile.TarInfo("index.html")
                content = b"artifact"
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
            ssh = _FakeSsh()
            fake_paramiko = types.SimpleNamespace(
                SSHClient=lambda: ssh,
                AutoAddPolicy=lambda: object(),
            )
            config = {
                "server": {"host": "example", "port": 22, "username": "user", "password": "secret"},
                "projects": [{"name": "project", "server_upload_path": "/srv/project"}],
            }

            with patch.dict(sys.modules, {"paramiko": fake_paramiko}):
                result = ServerUploader().upload(artifact, config, logging.getLogger(__name__), "project")

            self.assertTrue(result.success)
            self.assertEqual(result.target_url, "example:/srv/project")
            self.assertEqual(len(ssh.sftp.uploads), 1)
            self.assertTrue(any("/srv/project" in command for command in ssh.commands))

    def test_upload_falls_back_to_global_server_upload_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "project.tar.gz"
            with tarfile.open(artifact, "w:gz") as archive:
                info = tarfile.TarInfo("index.html")
                content = b"artifact"
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
            ssh = _FakeSsh()
            fake_paramiko = types.SimpleNamespace(
                SSHClient=lambda: ssh,
                AutoAddPolicy=lambda: object(),
            )
            config = {
                "server": {"host": "example", "port": 22, "username": "user", "password": "secret"},
                "server_upload_paths": {"fallback-proj": "/srv/fallback"},
                "projects": [{"name": "fallback-proj"}],
            }

            with patch.dict(sys.modules, {"paramiko": fake_paramiko}):
                result = ServerUploader().upload(artifact, config, logging.getLogger(__name__), "fallback-proj")

            self.assertTrue(result.success)
            self.assertEqual(result.target_url, "example:/srv/fallback")
            self.assertEqual(len(ssh.sftp.uploads), 1)
            self.assertTrue(any("/srv/fallback" in command for command in ssh.commands))

    def test_rejects_archive_entries_outside_target_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "malicious.tar.gz"
            with tarfile.open(artifact, "w:gz") as archive:
                info = tarfile.TarInfo("../escape.txt")
                content = b"escape"
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
            config = {
                "server": {"host": "example", "port": 22, "username": "user", "password": "secret"},
                "projects": [{"name": "project", "server_upload_path": "/srv/project"}],
            }

            result = ServerUploader().upload(artifact, config, logging.getLogger(__name__), "project")

            self.assertFalse(result.success)
            self.assertIn("不安全", result.message)


class TestSvnUploader(unittest.TestCase):
    def test_rejects_parent_path_segments(self):
        with self.assertRaises(ValueError):
            join_svn_url('https://svn.example/root', '..', 'project')

    def test_same_project_artifact_matching(self):
        # Same project matches
        self.assertTrue(_is_same_project_artifact("yarward-ntv-frontend_3.1.3_20260701.tar.gz", "yarward-ntv-frontend_3.1.4_20260803.tar.gz", "yarward-ntv-frontend"))
        self.assertTrue(_is_same_project_artifact("ntv_3.1.3.tar.gz", "yarward-ntv-frontend_3.1.4.tar.gz", "yarward-ntv-frontend"))
        # Identical filename is skipped (not an older artifact)
        self.assertFalse(_is_same_project_artifact("yarward-ntv-frontend_3.1.4.tar.gz", "yarward-ntv-frontend_3.1.4.tar.gz", "yarward-ntv-frontend"))
        # Different project should not match
        self.assertFalse(_is_same_project_artifact("yarward-his-frontend_1.0.tar.gz", "yarward-ntv-frontend_3.1.4.tar.gz", "yarward-ntv-frontend"))

    def test_as_log_fn_normalization(self):
        logs = []
        fn = as_log_fn(lambda msg: logs.append(msg))
        fn("test log")
        self.assertEqual(logs, ["test log"])

        logger = logging.getLogger("test_logger")
        with patch.object(logger, "info") as mock_info:
            fn2 = as_log_fn(logger)
            fn2("hello")
            mock_info.assert_called_once_with("%s", "hello")

        fn3 = as_log_fn(None)
        self.assertTrue(callable(fn3))
        # Should execute safely without raising
        fn3("noop log")

    def test_reports_svn_add_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / 'project.tar.gz'
            artifact.write_bytes(b'artifact')
            completed = types.SimpleNamespace(returncode=0, stdout='', stderr='')
            add_failed = types.SimpleNamespace(
                returncode=1, stdout='', stderr='svn add failed'
            )

            with patch(
                'uploaders.svn.run_process',
                side_effect=[completed, add_failed, completed],
            ), patch(
                'uploaders.svn.UPGRADE_DOC_PATH',
                Path(temp_dir) / 'missing.docx',
            ):
                result = upload_artifact(
                    artifact,
                    'https://svn.example/root/project/project.tar.gz',
                    username='user',
                    password='secret',
                )

            self.assertFalse(result.success)
            self.assertIn('SVN add failed', result.message)

    def test_upload_builds_hospital_order_and_project_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "project.tar.gz"
            artifact.write_bytes(b"artifact")
            config = {
                "svn_root": "https://svn.example/root",
                "svn_credentials": {"username": "user", "password": "secret"},
                "hospital_name": "医院 A",
                "order_no": "ORDER-1",
                "projects": [{"name": "project", "branch": "release", "svn_leaf": "web"}],
            }
            expected = UploadResult(True, "https://svn.example/target", "uploaded")

            with patch("uploaders.svn.ensure_svn_path") as ensure_path, patch(
                "uploaders.svn.upload_artifact", return_value=expected
            ) as upload_artifact:
                result = SvnUploader().upload(artifact, config, logging.getLogger(__name__), "project")

            self.assertTrue(result.success)
            ensure_path.assert_called_once()
            svn_url = upload_artifact.call_args.args[1]
            self.assertIn("%E5%8C%BB%E9%99%A2%20A/ORDER-1/web/project.tar.gz", svn_url)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Tests for workflow.cache module."""

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from unittest.mock import patch

from workflow.cache import BuildCache


class TestBuildCache(unittest.TestCase):
    """Tests for BuildCache class."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = BuildCache(Path(self.temp_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_input_hash_returns_string(self):
        """Test that compute_input_hash returns a hex string."""
        # Create a minimal project structure
        project_dir = Path(self.temp_dir) / "project"
        project_dir.mkdir()
        (project_dir / "deploy.sh").write_text("#!/bin/bash\necho hello")
        (project_dir / "package.json").write_text('{"name": "test"}')

        hash_val = self.cache.compute_input_hash(project_dir)
        self.assertIsInstance(hash_val, str)
        self.assertEqual(len(hash_val), 64)  # SHA-256 hex length

    def test_store_and_get_artifact(self):
        """Test storing and retrieving a cached artifact."""
        # Create a fake artifact
        artifact_dir = Path(self.temp_dir) / "artifacts"
        artifact_dir.mkdir()
        artifact_path = artifact_dir / "test.tar.gz"
        artifact_path.write_bytes(b"fake tarball content")

        input_hash = "abc123def456"

        # Store the artifact
        stored_path = self.cache.store_artifact(input_hash, artifact_path)
        self.assertTrue(stored_path.exists())
        self.assertEqual(stored_path.name, "test.tar.gz")

        # Retrieve the artifact
        cached = self.cache.get_cached_artifact(input_hash)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.name, "test.tar.gz")

    def test_has_cache(self):
        """Test has_cache method."""
        self.assertFalse(self.cache.has_cache("nonexistent"))

        # Store an artifact
        artifact_dir = Path(self.temp_dir) / "artifacts"
        artifact_dir.mkdir()
        artifact_path = artifact_dir / "test.tar.gz"
        artifact_path.write_bytes(b"content")

        self.cache.store_artifact("testhash", artifact_path)
        self.assertTrue(self.cache.has_cache("testhash"))

    def test_clear_cache(self):
        """Test clearing the cache."""
        # Store some artifacts
        artifact_dir = Path(self.temp_dir) / "artifacts"
        artifact_dir.mkdir()
        artifact_path = artifact_dir / "test.tar.gz"
        artifact_path.write_bytes(b"content")

        self.cache.store_artifact("hash1", artifact_path)
        self.cache.store_artifact("hash2", artifact_path)

        self.assertTrue(self.cache.has_cache("hash1"))
        self.assertTrue(self.cache.has_cache("hash2"))

        # Clear the cache - should remove hash1 and hash2 directories
        # Note: artifacts directory is also in temp_dir but not a cache entry
        count = self.cache.clear()
        self.assertGreaterEqual(count, 2)  # At least 2 cache entries
        self.assertFalse(self.cache.has_cache("hash1"))
        self.assertFalse(self.cache.has_cache("hash2"))

    def test_get_cached_zip_artifact(self):
        artifact_dir = Path(self.temp_dir) / "artifacts"
        artifact_dir.mkdir()
        artifact_path = artifact_dir / "app.zip"
        artifact_path.write_bytes(b"zip-content")

        self.cache.store_artifact("ziphash", artifact_path)
        cached = self.cache.get_cached_artifact("ziphash")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.name, "app.zip")

    @patch("workflow.cache.get_commit_sha", return_value="abc123def")
    def test_script_line_endings_do_not_change_hash(self, _mock_sha):
        project = Path(self.temp_dir) / "line-endings"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}', encoding="utf-8")
        (project / "deploy.sh").write_bytes(b"#!/bin/bash\r\necho hi\r\n")
        hash_crlf = self.cache.compute_input_hash(project)
        (project / "deploy.sh").write_bytes(b"#!/bin/bash\necho hi\n")
        hash_lf = self.cache.compute_input_hash(project)
        self.assertEqual(hash_crlf, hash_lf)

    @patch("workflow.cache.get_commit_sha", return_value="abc123def")
    def test_regular_build_ignores_sibling_micro_repos(self, _mock_sha):
        root = Path(self.temp_dir) / "repos"
        project = root / "yarward-ntv-frontend"
        sibling = root / "yarward-micro-menu"
        project.mkdir(parents=True)
        sibling.mkdir()
        (sibling / ".git").mkdir()
        (project / "package.json").write_text('{"name": "ntv"}', encoding="utf-8")
        (sibling / "package.json").write_text('{"name": "menu"}', encoding="utf-8")

        hash_before = self.cache.compute_input_hash(project, build_command="deploy.sh")
        (sibling / "package.json").write_text('{"name": "menu", "v": 2}', encoding="utf-8")
        hash_after = self.cache.compute_input_hash(project, build_command="deploy.sh")
        self.assertEqual(hash_before, hash_after)

    @patch("workflow.cache.get_commit_sha", return_value="abc123def")
    def test_micro_build_includes_sibling_manifests(self, _mock_sha):
        root = Path(self.temp_dir) / "micro-repos"
        project = root / "yarward-web-frontend"
        sibling = root / "yarward-micro-menu"
        project.mkdir(parents=True)
        sibling.mkdir()
        (sibling / ".git").mkdir()
        (project / "package.json").write_text('{"name": "web"}', encoding="utf-8")
        (sibling / "package.json").write_text('{"name": "menu"}', encoding="utf-8")

        hash_before = self.cache.compute_input_hash(
            project, build_command="deploy-micro.sh", target_branch="3.5.0"
        )
        (sibling / "package.json").write_text('{"name": "menu", "v": 2}', encoding="utf-8")
        hash_after = self.cache.compute_input_hash(
            project, build_command="deploy-micro.sh", target_branch="3.5.0"
        )
        self.assertNotEqual(hash_before, hash_after)

    @patch("workflow.cache.get_commit_sha", return_value="abc123def")
    def test_fingerprint_summary_omits_siblings_for_regular_build(self, _mock_sha):
        project = Path(self.temp_dir) / "plain"
        project.mkdir()
        (project / "package.json").write_text('{"name": "plain"}', encoding="utf-8")
        _digest, summary = self.cache.compute_input_fingerprint(project, build_command="deploy.sh")
        self.assertIn("siblings=none", summary)
        self.assertIn("commit=abc123de", summary)


if __name__ == "__main__":
    unittest.main()

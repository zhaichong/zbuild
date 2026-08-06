# -*- coding: utf-8 -*-
"""Tests for workflow.cache module."""

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

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


if __name__ == "__main__":
    unittest.main()

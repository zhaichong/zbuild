# -*- coding: utf-8 -*-
"""Tests for git.deps module."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from git.deps import (
    FINGERPRINT_FILE,
    dependency_fingerprint,
    dependency_install_command,
    ensure_dependencies,
)


class TestDependencyManagement(unittest.TestCase):
    """Tests for dependency fingerprinting and installation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dependency_fingerprint_changes_when_package_json_changes(self):
        """Fingerprint should change when package.json content changes."""
        pkg_file = self.project_dir / "package.json"
        pkg_file.write_text('{"dependencies": {"lodash": "^4.0.0"}}', encoding="utf-8")

        fp1 = dependency_fingerprint(self.project_dir)
        self.assertTrue(fp1.startswith("package.json:"))

        pkg_file.write_text('{"dependencies": {"lodash": "^4.0.0", "mitt": "^3.0.0"}}', encoding="utf-8")
        fp2 = dependency_fingerprint(self.project_dir)

        self.assertNotEqual(fp1, fp2)

    def test_dependency_fingerprint_empty_when_no_manifest(self):
        """Fingerprint should be empty string when no manifest file exists."""
        self.assertEqual(dependency_fingerprint(self.project_dir), "")

    def test_dependency_install_command(self):
        """Test default package manager install commands."""
        with patch("git.deps.package_manager_executable", return_value="npm"):
            cmd = dependency_install_command(self.project_dir)
            self.assertEqual(cmd, ["npm", "install"])

    @patch("git.deps.run_process_stream")
    def test_ensure_dependencies_skips_when_fingerprint_matches(self, mock_run):
        """Should skip install when node_modules and fingerprint match."""
        node_modules = self.project_dir / "node_modules"
        node_modules.mkdir()
        pkg_file = self.project_dir / "package.json"
        pkg_file.write_text('{"name": "test"}', encoding="utf-8")

        fp = dependency_fingerprint(self.project_dir)
        (node_modules / FINGERPRINT_FILE).write_text(fp, encoding="utf-8")

        result = ensure_dependencies(self.project_dir)
        self.assertTrue(result)
        mock_run.assert_not_called()

    @patch("git.deps.run_process_stream")
    def test_ensure_dependencies_installs_when_fingerprint_differs(self, mock_run):
        """Should run install and update fingerprint when package.json changes."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")

        node_modules = self.project_dir / "node_modules"
        node_modules.mkdir()
        pkg_file = self.project_dir / "package.json"
        pkg_file.write_text('{"name": "test", "v": 1}', encoding="utf-8")

        # Old fingerprint recorded
        (node_modules / FINGERPRINT_FILE).write_text("package.json:oldhash", encoding="utf-8")

        # Now package.json changed
        pkg_file.write_text('{"name": "test", "v": 2}', encoding="utf-8")
        current_fp = dependency_fingerprint(self.project_dir)

        result = ensure_dependencies(self.project_dir)
        self.assertTrue(result)
        mock_run.assert_called_once()

        # Check new fingerprint written
        saved_fp = (node_modules / FINGERPRINT_FILE).read_text(encoding="utf-8")
        self.assertEqual(saved_fp, current_fp)

    @patch("git.deps.run_process_stream")
    def test_ensure_dependencies_force_reinstalls(self, mock_run):
        """force=True should trigger install even if fingerprint matches."""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")

        node_modules = self.project_dir / "node_modules"
        node_modules.mkdir()
        pkg_file = self.project_dir / "package.json"
        pkg_file.write_text('{"name": "test"}', encoding="utf-8")

        fp = dependency_fingerprint(self.project_dir)
        (node_modules / FINGERPRINT_FILE).write_text(fp, encoding="utf-8")

        result = ensure_dependencies(self.project_dir, force=True)
        self.assertTrue(result)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

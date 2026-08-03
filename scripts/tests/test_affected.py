# -*- coding: utf-8 -*-
"""Tests for git.affected module."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import unittest
from unittest.mock import patch, MagicMock

from git.affected import (
    _changed_files,
    _map_file_to_project,
    find_affected_projects,
    find_affected_projects_from_staged,
)


class TestChangedFiles(unittest.TestCase):
    """Tests for _changed_files function."""

    @patch("git.affected.run_process")
    def test_changed_files_success(self, mock_run):
        """Test _changed_files with successful git diff."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.py\nfile2.py\n"
        mock_run.return_value = mock_result

        files = _changed_files("/repo", "main", "HEAD")
        self.assertEqual(files, ["file1.py", "file2.py"])

    @patch("git.affected.run_process")
    def test_changed_files_failure(self, mock_run):
        """Test _changed_files with failed git diff."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        files = _changed_files("/repo", "main", "HEAD")
        self.assertEqual(files, [])

    @patch("git.affected.run_process")
    def test_changed_files_empty(self, mock_run):
        """Test _changed_files with no changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        files = _changed_files("/repo", "main", "HEAD")
        self.assertEqual(files, [])


class TestMapFileToProject(unittest.TestCase):
    """Tests for _map_file_to_project function."""

    def test_map_file_to_project(self):
        """Test mapping a file to its project."""
        project_dirs = {
            "project-a": Path("project-a"),
            "project-b": Path("project-b"),
        }

        result = _map_file_to_project("project-a/src/index.js", project_dirs)
        self.assertEqual(result, "project-a")

    def test_map_file_to_project_no_match(self):
        """Test mapping a file that doesn't belong to any project."""
        project_dirs = {
            "project-a": Path("project-a"),
        }

        result = _map_file_to_project("other/file.js", project_dirs)
        self.assertIsNone(result)


class TestFindAffectedProjects(unittest.TestCase):
    """Tests for find_affected_projects function."""

    @patch("git.affected._changed_files")
    def test_find_affected_projects(self, mock_changed):
        """Test finding affected projects."""
        mock_changed.return_value = [
            "project-a/src/index.js",
            "project-b/src/main.js",
        ]

        project_dirs = {
            "project-a": Path("project-a"),
            "project-b": Path("project-b"),
            "project-c": Path("project-c"),
        }

        affected = find_affected_projects("/repo", project_dirs)
        self.assertEqual(sorted(affected), ["project-a", "project-b"])

    @patch("git.affected._changed_files")
    def test_find_affected_projects_shared_file(self, mock_changed):
        """Test that shared files mark all projects as affected."""
        mock_changed.return_value = ["package.json"]

        project_dirs = {
            "project-a": Path("project-a"),
            "project-b": Path("project-b"),
        }

        affected = find_affected_projects("/repo", project_dirs)
        self.assertEqual(sorted(affected), ["project-a", "project-b"])

    @patch("git.affected._changed_files")
    def test_find_affected_projects_no_changes(self, mock_changed):
        """Test with no changes."""
        mock_changed.return_value = []

        project_dirs = {"project-a": Path("project-a")}

        affected = find_affected_projects("/repo", project_dirs)
        self.assertEqual(affected, [])


class TestFindAffectedProjectsFromStaged(unittest.TestCase):
    """Tests for find_affected_projects_from_staged function."""

    @patch("git.affected.run_process")
    def test_find_affected_from_staged(self, mock_run):
        """Test finding affected projects from staged changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "project-a/src/index.js\n"
        mock_run.return_value = mock_result

        project_dirs = {
            "project-a": Path("project-a"),
            "project-b": Path("project-b"),
        }

        affected = find_affected_projects_from_staged("/repo", project_dirs)
        self.assertEqual(affected, ["project-a"])


if __name__ == "__main__":
    unittest.main()

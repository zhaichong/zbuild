# -*- coding: utf-8 -*-
"""Tests for core.models module."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.models import (
    StepStatus,
    LogEntry,
    StepRecord,
    BuildArtifact,
    ProjectRunRecord,
    ExecutionRecord,
    TaskTemplate,
)


class TestStepStatus(unittest.TestCase):
    """Tests for StepStatus enum."""

    def test_status_values(self):
        """Test that all expected status values exist."""
        self.assertEqual(StepStatus.PENDING.value, "pending")
        self.assertEqual(StepStatus.RUNNING.value, "running")
        self.assertEqual(StepStatus.SUCCESS.value, "success")
        self.assertEqual(StepStatus.FAILED.value, "failed")
        self.assertEqual(StepStatus.SKIPPED.value, "skipped")
        self.assertEqual(StepStatus.RETRYING.value, "retrying")

    def test_is_terminal(self):
        """Test is_terminal method."""
        self.assertTrue(StepStatus.SUCCESS.is_terminal())
        self.assertTrue(StepStatus.FAILED.is_terminal())
        self.assertTrue(StepStatus.SKIPPED.is_terminal())
        self.assertFalse(StepStatus.PENDING.is_terminal())
        self.assertFalse(StepStatus.RUNNING.is_terminal())


class TestLogEntry(unittest.TestCase):
    """Tests for LogEntry model."""

    def test_log_entry_creation(self):
        """Test creating a LogEntry."""
        entry = LogEntry(
            timestamp=time.time(),
            level="info",
            message="Test message",
        )
        self.assertEqual(entry.level, "info")
        self.assertEqual(entry.message, "Test message")

    def test_log_entry_to_dict(self):
        """Test LogEntry serialization."""
        entry = LogEntry(
            timestamp=1234567890.0,
            level="error",
            message="Error occurred",
        )
        d = entry.to_dict()
        self.assertEqual(d["level"], "error")
        self.assertEqual(d["message"], "Error occurred")
        self.assertEqual(d["timestamp"], 1234567890.0)

    def test_log_entry_from_dict(self):
        """Test LogEntry deserialization."""
        data = {"timestamp": 123.0, "level": "warn", "message": "Warning"}
        entry = LogEntry.from_dict(data)
        self.assertEqual(entry.timestamp, 123.0)
        self.assertEqual(entry.level, "warn")


class TestStepRecord(unittest.TestCase):
    """Tests for StepRecord model."""

    def test_step_record_creation(self):
        """Test creating a StepRecord."""
        record = StepRecord(
            name="Test Step",
            status=StepStatus.PENDING,
            max_retries=2,
        )
        self.assertEqual(record.name, "Test Step")
        self.assertEqual(record.status, StepStatus.PENDING)
        self.assertEqual(record.max_retries, 2)

    def test_step_record_to_dict(self):
        """Test StepRecord serialization."""
        record = StepRecord(
            name="Build",
            status=StepStatus.SUCCESS,
            message="Build completed",
            attempts=1,
            duration_seconds=5.5,
        )
        d = record.to_dict()
        self.assertEqual(d["name"], "Build")
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["message"], "Build completed")


class TestBuildArtifact(unittest.TestCase):
    """Tests for BuildArtifact model."""

    def test_artifact_creation(self):
        """Test creating a BuildArtifact."""
        artifact = BuildArtifact(
            path="/path/to/artifact.tar.gz",
            size_bytes=1024,
        )
        self.assertEqual(artifact.path, "/path/to/artifact.tar.gz")
        self.assertEqual(artifact.size_bytes, 1024)

    def test_artifact_to_dict(self):
        """Test BuildArtifact serialization."""
        artifact = BuildArtifact(
            path="/test.tar.gz",
            sha256="abc123",
            size_bytes=2048,
            created_at=1234567890.0,
        )
        d = artifact.to_dict()
        self.assertEqual(d["path"], "/test.tar.gz")
        self.assertEqual(d["sha256"], "abc123")
        self.assertEqual(d["size_bytes"], 2048)


class TestExecutionRecord(unittest.TestCase):
    """Tests for ExecutionRecord model."""

    def test_execution_record_creation(self):
        """Test creating an ExecutionRecord."""
        record = ExecutionRecord(
            run_id="abc123",
            mode="svn",
            started_at=time.time(),
        )
        self.assertEqual(record.run_id, "abc123")
        self.assertEqual(record.mode, "svn")

    def test_execution_record_to_dict(self):
        """Test ExecutionRecord serialization."""
        record = ExecutionRecord(
            run_id="test123",
            mode="server",
            started_at=1234567890.0,
            finished_at=1234567900.0,
            success=True,
        )
        d = record.to_dict()
        self.assertEqual(d["run_id"], "test123")
        self.assertEqual(d["mode"], "server")
        self.assertTrue(d["success"])
        self.assertEqual(d["duration_seconds"], 10.0)


class TestTaskTemplate(unittest.TestCase):
    """Tests for TaskTemplate model."""

    def test_template_creation(self):
        """Test creating a TaskTemplate."""
        template = TaskTemplate(
            template_id="tmpl-001",
            name="Test Template",
            description="A test template",
            config={"mode": "svn"},
        )
        self.assertEqual(template.template_id, "tmpl-001")
        self.assertEqual(template.name, "Test Template")

    def test_template_to_dict(self):
        """Test TaskTemplate serialization."""
        template = TaskTemplate(
            template_id="tmpl-002",
            name="SVN Build",
            config={"uploadAfterBuild": True},
        )
        d = template.to_dict()
        self.assertEqual(d["template_id"], "tmpl-002")
        self.assertEqual(d["name"], "SVN Build")
        self.assertTrue(d["config"]["uploadAfterBuild"])

    def test_template_from_dict(self):
        """Test TaskTemplate deserialization."""
        data = {
            "template_id": "tmpl-003",
            "name": "Server Build",
            "description": "Build and upload to server",
            "mode": "server",
            "config": {},
        }
        template = TaskTemplate.from_dict(data)
        self.assertEqual(template.template_id, "tmpl-003")
        self.assertEqual(template.mode, "server")


if __name__ == "__main__":
    unittest.main()

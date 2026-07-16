# -*- coding: utf-8 -*-
"""Data models for build tracking, execution records, and templates."""
from __future__ import annotations

import enum
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Step status state machine (inspired by Jenkins Pipeline)
# ---------------------------------------------------------------------------

class StepStatus(str, enum.Enum):
    """Lifecycle states for a workflow step."""
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILED   = "failed"
    SKIPPED  = "skipped"
    RETRYING = "retrying"

    def is_terminal(self) -> bool:
        return self in (StepStatus.SUCCESS, StepStatus.FAILED, StepStatus.SKIPPED)


# ---------------------------------------------------------------------------
# Log entry
# ---------------------------------------------------------------------------

@dataclass
class LogEntry:
    """Single timestamped log line."""
    timestamp: float
    level: str          # "info" | "warn" | "error" | "debug"
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        return cls(
            timestamp=data["timestamp"],
            level=data["level"],
            message=data["message"],
        )


# ---------------------------------------------------------------------------
# Step record
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """Execution record for a single workflow step."""
    name: str
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0
    max_retries: int = 0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    duration_seconds: float = 0.0
    message: str = ""
    logs: list[LogEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "message": self.message,
            "logs": [log.to_dict() for log in self.logs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepRecord":
        return cls(
            name=data["name"],
            status=StepStatus(data.get("status", "pending")),
            attempts=data.get("attempts", 0),
            max_retries=data.get("max_retries", 0),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            duration_seconds=data.get("duration_seconds", 0.0),
            message=data.get("message", ""),
            logs=[LogEntry.from_dict(log) for log in data.get("logs", [])],
        )


# ---------------------------------------------------------------------------
# Build artifact
# ---------------------------------------------------------------------------

@dataclass
class BuildArtifact:
    """Represents a built artifact (tar.gz) with content hash."""
    path: str
    sha256: str = ""
    size_bytes: int = 0
    created_at: float = 0.0

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the artifact file."""
        p = Path(self.path)
        if not p.exists():
            return ""
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        self.sha256 = h.hexdigest()
        self.size_bytes = p.stat().st_size
        return self.sha256

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuildArtifact":
        return cls(
            path=data["path"],
            sha256=data.get("sha256", ""),
            size_bytes=data.get("size_bytes", 0),
            created_at=data.get("created_at", 0.0),
        )


# ---------------------------------------------------------------------------
# Project run record
# ---------------------------------------------------------------------------

@dataclass
class ProjectRunRecord:
    """Execution record for a single project within a run."""
    project_name: str
    branch: str
    steps: list[StepRecord] = field(default_factory=list)
    artifact: Optional[BuildArtifact] = None
    target_url: str = ""
    success: bool = False
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "branch": self.branch,
            "steps": [s.to_dict() for s in self.steps],
            "artifact": self.artifact.to_dict() if self.artifact else None,
            "target_url": self.target_url,
            "success": self.success,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectRunRecord":
        return cls(
            project_name=data["project_name"],
            branch=data["branch"],
            steps=[StepRecord.from_dict(s) for s in data.get("steps", [])],
            artifact=BuildArtifact.from_dict(data["artifact"]) if data.get("artifact") else None,
            target_url=data.get("target_url", ""),
            success=data.get("success", False),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            error_message=data.get("error_message", ""),
        )


# ---------------------------------------------------------------------------
# Execution record (top-level, one per pipeline run)
# ---------------------------------------------------------------------------

@dataclass
class ExecutionRecord:
    """Top-level record for a complete pipeline execution."""
    run_id: str
    mode: str               # "svn" | "server" | "local"
    projects: list[ProjectRunRecord] = field(default_factory=list)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    success: bool = False
    config_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "projects": [p.to_dict() for p in self.projects],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "config_snapshot": self.config_snapshot,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionRecord":
        return cls(
            run_id=data["run_id"],
            mode=data["mode"],
            projects=[ProjectRunRecord.from_dict(p) for p in data.get("projects", [])],
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            success=data.get("success", False),
            config_snapshot=data.get("config_snapshot", {}),
        )


# ---------------------------------------------------------------------------
# Task template (inspired by Semaphore UI)
# ---------------------------------------------------------------------------

@dataclass
class TaskTemplate:
    """Reusable configuration template for quick pipeline launches."""
    template_id: str
    name: str
    description: str = ""
    mode: str = "svn"
    config: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "mode": self.mode,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskTemplate":
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data.get("description", ""),
            mode=data.get("mode", "svn"),
            config=data.get("config", {}),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
        )

    @classmethod
    def from_current_config(cls, template_id: str, name: str,
                            config: dict[str, Any], mode: str = "svn",
                            description: str = "") -> "TaskTemplate":
        """Create a template snapshot from the current configuration."""
        now = time.time()
        return cls(
            template_id=template_id,
            name=name,
            description=description,
            mode=mode,
            config=config.copy(),
            created_at=now,
            updated_at=now,
        )

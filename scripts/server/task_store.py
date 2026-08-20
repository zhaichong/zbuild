# -*- coding: utf-8 -*-
"""SQLite persistence for queued Web tasks, events, artifacts, and audit entries."""

import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from server.secrets import (
    DpapiSecretCodec,
    SecretCodec,
    decrypt_secret_json,
    encrypt_secret_json,
    merge_secrets,
    split_secrets,
)

TASK_STATUSES = {
    "queued", "preparing", "running", "success", "failed", "cancelled", "interrupted"
}
TERMINAL_STATUSES = {"success", "failed", "cancelled", "interrupted"}
_PRIVATE_RESULT_KEYS = {
    "payload", "config", "_trusted_projects", "baserepo", "worktree",
    "path", "repopath", "rootpath", "root_path",
}
_WINDOWS_PATH = re.compile(r"(?i)\b[a-z]:[\\/][^\s'\";,]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _public_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _public_value(item)
            for key, item in value.items()
            if str(key).lower() not in _PRIVATE_RESULT_KEYS
            and not str(key).lower().endswith("path")
        }
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, str):
        if Path(value).is_absolute():
            return "[path]"
        return _WINDOWS_PATH.sub("[path]", value)
    return value


class TaskStore:
    def __init__(self, data_dir: Path, codec: Optional[SecretCodec] = None):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = self.data_dir / "task-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.codec = codec or DpapiSecretCodec()
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.data_dir / "tasks.db", check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self) -> None:
        with self._db:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    queue_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    request_id TEXT NOT NULL UNIQUE,
                    task_type TEXT NOT NULL,
                    submitter TEXT NOT NULL,
                    profile_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    secret_ciphertext TEXT NOT NULL DEFAULT '',
                    result_json TEXT,
                    commits_json TEXT NOT NULL DEFAULT '[]',
                    error TEXT,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    task_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (task_id, seq),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    mime_type TEXT,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS audit (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    action TEXT NOT NULL,
                    submitter TEXT,
                    remote_ip TEXT,
                    result TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            columns = {row[1] for row in self._db.execute("PRAGMA table_info(tasks)")}
            if "commits_json" not in columns:
                self._db.execute(
                    "ALTER TABLE tasks ADD COLUMN commits_json TEXT NOT NULL DEFAULT '[]'"
                )
            if "profile_id" not in columns:
                self._db.execute(
                    "ALTER TABLE tasks ADD COLUMN profile_id TEXT NOT NULL DEFAULT ''"
                )
            self._db.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_profile_created "
                "ON tasks(profile_id, created_at DESC)"
            )

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def create_task(
        self, request_id: str, task_type: str, submitter: str, payload: Dict[str, Any],
        profile_id: str = "",
    ) -> Tuple[Dict[str, Any], bool]:
        with self._lock:
            existing = self._db.execute(
                "SELECT * FROM tasks WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing:
                public_payload, _ = split_secrets(payload)
                if (
                    existing["task_type"] != task_type
                    or existing["submitter"] != submitter
                    or existing["profile_id"] != profile_id
                    or json.loads(existing["payload_json"]) != public_payload
                ):
                    raise ValueError("requestId was already used for a different task")
                return self._task_from_row(existing, detail=False), False
            public_payload, secrets = split_secrets(payload)
            ciphertext = encrypt_secret_json(self.codec, secrets)
            timestamp = _now()
            task_id = uuid.uuid4().hex
            with self._db:
                self._db.execute(
                    """INSERT INTO tasks
                       (task_id, request_id, task_type, submitter, profile_id, status, payload_json,
                        secret_ciphertext, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?, ?)""",
                    (
                        task_id, request_id, task_type, submitter, profile_id,
                        json.dumps(public_payload, ensure_ascii=False), ciphertext,
                        timestamp, timestamp,
                    ),
                )
            return self.get_task(task_id, detail=False), True

    def _task_from_row(self, row: sqlite3.Row, detail: bool) -> Dict[str, Any]:
        payload = json.loads(row["payload_json"])
        projects = [
            {"name": item.get("name", ""), "branch": item.get("branch", "")}
            for item in payload.get("projects", []) if isinstance(item, dict)
        ]
        task = {
            "taskId": row["task_id"],
            "requestId": row["request_id"],
            "type": row["task_type"],
            "submitter": row["submitter"],
            "status": row["status"],
            "queueSeq": row["queue_seq"],
            "queuePosition": self._queue_position(row["queue_seq"])
            if row["status"] == "queued" else None,
            "projects": projects,
            "createdAt": row["created_at"],
            "startedAt": row["started_at"],
            "finishedAt": row["finished_at"],
            "error": _public_value(row["error"]),
        }
        if detail:
            task.update({
                "result": _public_value(
                    json.loads(row["result_json"]) if row["result_json"] else None
                ),
                "commits": json.loads(row["commits_json"] or "[]"),
                "lastSeq": self.last_seq(row["task_id"]),
                "artifacts": self.list_artifacts(row["task_id"]),
            })
        return task

    def _queue_position(self, queue_seq: int) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) AS count FROM tasks WHERE status='queued' AND queue_seq<=?",
            (queue_seq,),
        ).fetchone()
        return int(row["count"])

    def get_task(
        self, task_id: str, detail: bool = True, profile_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            query = "SELECT * FROM tasks WHERE task_id = ?"
            params: List[Any] = [task_id]
            if profile_id is not None:
                query += " AND profile_id = ?"
                params.append(profile_id)
            row = self._db.execute(query, params).fetchone()
            return self._task_from_row(row, detail) if row else None

    def get_execution_payload(self, task_id: str) -> Dict[str, Any]:
        with self._lock:
            row = self._db.execute(
                "SELECT payload_json, secret_ciphertext FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not row:
                raise KeyError(task_id)
            public = json.loads(row["payload_json"])
            secrets = decrypt_secret_json(self.codec, row["secret_ciphertext"])
            return merge_secrets(public, secrets)

    def clear_execution_secrets(self, task_id: str) -> None:
        """Remove the task-only credential snapshot after it reaches a terminal state."""
        with self._lock, self._db:
            self._db.execute(
                "UPDATE tasks SET secret_ciphertext='' WHERE task_id=? AND status IN "
                "('success', 'failed', 'cancelled', 'interrupted')",
                (task_id,),
            )

    def set_status(
        self, task_id: str, status: str, *, error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if status not in TASK_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        timestamp = _now()
        error = self.redact(task_id, error) if error else error
        result = self.redact(task_id, result) if result is not None else result
        started_at = timestamp if status == "running" else None
        finished_at = timestamp if status in TERMINAL_STATUSES else None
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT status, cancel_requested FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if not row:
                raise KeyError(task_id)
            if row["status"] in TERMINAL_STATUSES:
                return self.get_task(task_id, detail=False)
            if row["cancel_requested"] and status not in TERMINAL_STATUSES:
                status = "cancelled"
                finished_at = timestamp
            self._db.execute(
                """UPDATE tasks SET status=?, error=COALESCE(?, error),
                   result_json=COALESCE(?, result_json), updated_at=?,
                   started_at=COALESCE(?, started_at), finished_at=COALESCE(?, finished_at)
                   WHERE task_id=?""",
                (
                    status, error,
                    json.dumps(result, ensure_ascii=False) if result is not None else None,
                    timestamp, started_at, finished_at, task_id,
                ),
            )
        return self.get_task(task_id, detail=False)

    def append_event(self, task_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = self.redact(task_id, payload)
        with self._lock, self._db:
            if not self._db.execute(
                "SELECT 1 FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone():
                raise KeyError(task_id)
            seq = self.last_seq(task_id) + 1
            timestamp = _now()
            payload_json = json.dumps(payload, ensure_ascii=False)
            self._db.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                (task_id, seq, event_type, timestamp, payload_json),
            )
        event = {
            "taskId": task_id, "seq": seq, "type": event_type,
            "timestamp": timestamp, "payload": payload,
        }
        with (self.log_dir / f"{task_id}.ndjson").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def redact(self, task_id: str, value: Any) -> Any:
        with self._lock:
            row = self._db.execute(
                "SELECT secret_ciphertext FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if not row or not row["secret_ciphertext"]:
            return value
        secret_tree = decrypt_secret_json(self.codec, row["secret_ciphertext"])
        secrets: List[str] = []

        def collect(item: Any) -> None:
            if isinstance(item, dict):
                for nested in item.values():
                    collect(nested)
            elif isinstance(item, list):
                for nested in item:
                    collect(nested)
            elif isinstance(item, str) and item:
                secrets.append(item)

        collect(secret_tree)

        def clean(item: Any) -> Any:
            if isinstance(item, dict):
                return {key: clean(nested) for key, nested in item.items()}
            if isinstance(item, list):
                return [clean(nested) for nested in item]
            if isinstance(item, str):
                for secret in secrets:
                    item = item.replace(secret, "[redacted]")
            return item

        return clean(value)

    def last_seq(self, task_id: str) -> int:
        row = self._db.execute(
            "SELECT COALESCE(MAX(seq), 0) AS seq FROM events WHERE task_id = ?", (task_id,)
        ).fetchone()
        return int(row["seq"] if row else 0)

    def list_events(self, task_id: str, after: int = 0) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM events WHERE task_id=? AND seq>? ORDER BY seq", (task_id, after)
            ).fetchall()
        return [{
            "taskId": row["task_id"], "seq": row["seq"], "type": row["event_type"],
            "timestamp": row["timestamp"], "payload": json.loads(row["payload_json"]),
        } for row in rows]

    def list_queued_ids(self) -> List[str]:
        with self._lock:
            rows = self._db.execute(
                "SELECT task_id FROM tasks WHERE status='queued' ORDER BY queue_seq"
            ).fetchall()
            return [row["task_id"] for row in rows]

    def list_tasks(
        self, status: Optional[str] = None, submitter: Optional[str] = None,
        created_after: Optional[str] = None, created_before: Optional[str] = None,
        limit: int = 100, offset: int = 0, profile_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if status:
            if status not in TASK_STATUSES:
                raise ValueError(f"Invalid task status: {status}")
            clauses.append("status = ?")
            params.append(status)
        if submitter:
            clauses.append("submitter = ?")
            params.append(submitter)
        if profile_id is not None:
            clauses.append("profile_id = ?")
            params.append(profile_id)
        if created_after:
            clauses.append("created_at >= ?")
            params.append(created_after)
        if created_before:
            clauses.append("created_at <= ?")
            params.append(created_before)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError("limit must be 1-200 and offset must not be negative")
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM tasks" + where
                + " ORDER BY created_at DESC, queue_seq DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            return [self._task_from_row(row, detail=False) for row in rows]

    def request_cancel(self, task_id: str, profile_id: Optional[str] = None) -> Dict[str, Any]:
        timestamp = _now()
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT status FROM tasks WHERE task_id=?"
                + (" AND profile_id=?" if profile_id is not None else ""),
                (task_id, profile_id) if profile_id is not None else (task_id,),
            ).fetchone()
            if not row:
                raise KeyError(task_id)
            if row["status"] in TERMINAL_STATUSES:
                raise ValueError("Task is already terminal")
            if row["status"] == "queued":
                self._db.execute(
                    """UPDATE tasks SET cancel_requested=1, status='cancelled',
                       updated_at=?, finished_at=? WHERE task_id=?""",
                    (timestamp, timestamp, task_id),
                )
            else:
                self._db.execute(
                    "UPDATE tasks SET cancel_requested=1, updated_at=? WHERE task_id=?",
                    (timestamp, task_id),
                )
        return self.get_task(task_id, detail=False, profile_id=profile_id)

    def is_cancel_requested(self, task_id: str) -> bool:
        with self._lock:
            row = self._db.execute(
                "SELECT cancel_requested FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
            return bool(row and row["cancel_requested"])

    def record_audit(
        self, action: str, result: str, *, task_id: Optional[str] = None,
        submitter: Optional[str] = None, remote_ip: Optional[str] = None,
    ) -> None:
        with self._lock, self._db:
            self._db.execute(
                """INSERT INTO audit(task_id, action, submitter, remote_ip, result, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, action, submitter, remote_ip, result, _now()),
            )

    def recover_after_restart(self) -> None:
        timestamp = _now()
        with self._lock, self._db:
            self._db.execute(
                """UPDATE tasks SET status='interrupted', updated_at=?, finished_at=?,
                   error=COALESCE(error, 'Service restarted while task was active')
                   WHERE status IN ('preparing', 'running')""",
                (timestamp, timestamp),
            )

    def list_artifacts(self, task_id: str) -> List[Dict[str, Any]]:
        rows = self._db.execute(
            "SELECT * FROM artifacts WHERE task_id=? ORDER BY created_at", (task_id,)
        ).fetchall()
        return [{
            "artifactId": row["artifact_id"], "name": row["name"],
            "mimeType": row["mime_type"], "sizeBytes": row["size_bytes"],
            "createdAt": row["created_at"],
        } for row in rows]

    def set_commits(self, task_id: str, commits: List[Dict[str, str]]) -> None:
        with self._lock, self._db:
            cursor = self._db.execute(
                "UPDATE tasks SET commits_json=?, updated_at=? WHERE task_id=?",
                (json.dumps(commits, ensure_ascii=False), _now(), task_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(task_id)

    def add_artifact(
        self, task_id: str, name: str, path: Path, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        resolved = Path(path).resolve()
        artifact_id = uuid.uuid4().hex
        with self._lock, self._db:
            if not self._db.execute(
                "SELECT 1 FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone():
                raise KeyError(task_id)
            self._db.execute(
                """INSERT INTO artifacts
                   (artifact_id, task_id, name, path, mime_type, size_bytes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (artifact_id, task_id, name, str(resolved), mime_type,
                 resolved.stat().st_size, _now()),
            )
        return next(item for item in self.list_artifacts(task_id)
                    if item["artifactId"] == artifact_id)

    def get_artifact_path(self, task_id: str, artifact_id: str) -> Optional[Path]:
        with self._lock:
            row = self._db.execute(
                "SELECT path FROM artifacts WHERE task_id=? AND artifact_id=?",
                (task_id, artifact_id),
            ).fetchone()
        return Path(row["path"]).resolve() if row else None

    def maintenance_candidates(
        self, workspace_days: int = 1, artifact_days: int = 30, task_days: int = 90
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        workspace_cutoff = (now - timedelta(days=workspace_days)).isoformat().replace("+00:00", "Z")
        artifact_cutoff = (now - timedelta(days=artifact_days)).isoformat().replace("+00:00", "Z")
        task_cutoff = (now - timedelta(days=task_days)).isoformat().replace("+00:00", "Z")
        with self._lock, self._db:
            workspaces = [row["task_id"] for row in self._db.execute(
                """SELECT task_id FROM tasks WHERE status IN ('success','failed','cancelled','interrupted')
                   AND finished_at IS NOT NULL AND finished_at < ?""", (workspace_cutoff,)
            )]
            artifact_rows = self._db.execute(
                "SELECT artifact_id, path FROM artifacts WHERE created_at < ?", (artifact_cutoff,)
            ).fetchall()
            artifact_paths = [row["path"] for row in artifact_rows]
            if artifact_rows:
                self._db.executemany(
                    "DELETE FROM artifacts WHERE artifact_id=?",
                    [(row["artifact_id"],) for row in artifact_rows],
                )
            expired_tasks = [row["task_id"] for row in self._db.execute(
                """SELECT task_id FROM tasks WHERE status IN ('success','failed','cancelled','interrupted')
                   AND finished_at IS NOT NULL AND finished_at < ?""", (task_cutoff,)
            )]
            expired_logs = [row["task_id"] for row in self._db.execute(
                """SELECT task_id FROM tasks WHERE status IN ('success','failed','cancelled','interrupted')
                   AND finished_at IS NOT NULL AND finished_at < ?""", (artifact_cutoff,)
            )]
            if expired_tasks:
                self._db.executemany(
                    "DELETE FROM tasks WHERE task_id=?", [(item,) for item in expired_tasks]
                )
            self._db.execute("DELETE FROM audit WHERE timestamp < ?", (task_cutoff,))
        return {
            "workspaceTaskIds": workspaces,
            "artifactPaths": artifact_paths,
            "expiredTaskIds": expired_tasks,
            "expiredLogTaskIds": expired_logs,
        }

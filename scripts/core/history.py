# -*- coding: utf-8 -*-
"""Build history store.

Manages per-run JSON records in HISTORY_DIR with an index.json for
fast listing without scanning all files.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.constants import HISTORY_DIR
from core.models import ExecutionRecord
from core.secrets import without_secrets


class HistoryStore:
    """CRUD operations for execution history records.

    Each run is stored as ``{HISTORY_DIR}/{run_id}.json`` and an
    ``index.json`` file maintains a summary list for fast access.
    """

    def __init__(self, history_dir: Optional[Path] = None) -> None:
        self.history_dir = history_dir or HISTORY_DIR
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.history_dir / "index.json"

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _load_index(self) -> List[Dict[str, Any]]:
        if not self._index_path.exists():
            return []
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save_index(self, index: List[Dict[str, Any]]) -> None:
        self._index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, record: ExecutionRecord) -> str:
        """Save a new execution record and update the index.

        Returns the run_id.
        """
        if not record.run_id:
            record.run_id = uuid.uuid4().hex[:12]
        if not record.started_at:
            record.started_at = time.time()

        record_data = record.to_dict()
        record_data["config_snapshot"] = without_secrets(record.config_snapshot)
        path = self.history_dir / f"{record.run_id}.json"
        path.write_text(
            json.dumps(record_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Update index
        index = self._load_index()
        index.insert(0, {
            "run_id": record.run_id,
            "mode": record.mode,
            "started_at": record.started_at,
            "success": record.success,
            "project_count": len(record.projects),
            "projects": [p.to_dict() for p in record.projects],
            "config_snapshot": record_data["config_snapshot"],
        })
        self._save_index(index)
        return record.run_id

    def update(self, record: ExecutionRecord) -> None:
        """Overwrite an existing execution record and refresh the index."""
        record_data = record.to_dict()
        record_data["config_snapshot"] = without_secrets(record.config_snapshot)
        path = self.history_dir / f"{record.run_id}.json"
        path.write_text(
            json.dumps(record_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        index = self._load_index()
        for entry in index:
            if entry.get("run_id") == record.run_id:
                entry["success"] = record.success
                entry["finished_at"] = record.finished_at
                entry["project_count"] = len(record.projects)
                entry["projects"] = [p.to_dict() for p in record.projects]
                entry["config_snapshot"] = record_data["config_snapshot"]
                if record.started_at and record.finished_at:
                    entry["duration_seconds"] = record.finished_at - record.started_at
                break
        self._save_index(index)

    def get(self, run_id: str) -> Optional[ExecutionRecord]:
        """Load a single execution record by run_id."""
        path = self.history_dir / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ExecutionRecord.from_dict(data)
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def list(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Return a summary list of execution records, newest first."""
        index = self._load_index()
        return index[offset:offset + limit]

    def delete(self, run_id: str) -> bool:
        """Delete an execution record and remove it from the index."""
        path = self.history_dir / f"{run_id}.json"
        existed = path.exists()
        if existed:
            path.unlink(missing_ok=True)

        index = self._load_index()
        index = [e for e in index if e.get("run_id") != run_id]
        self._save_index(index)
        return existed

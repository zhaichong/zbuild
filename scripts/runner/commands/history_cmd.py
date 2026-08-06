# -*- coding: utf-8 -*-
"""Commands: history-list, history-get."""

from typing import Any, Dict

from runner.cli import register
from core.history import HistoryStore


@register("history-list")
def cmd_history_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List execution history records."""
    limit = payload.get("limit", 50)
    offset = payload.get("offset", 0)
    store = HistoryStore()
    records = store.list(limit=limit, offset=offset)
    return {"success": True, "records": records}


@register("history-get")
def cmd_history_get(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Get a single execution record by run_id."""
    run_id = payload.get("id", "")
    if not run_id:
        return {"success": False, "error": "Missing 'id'"}

    store = HistoryStore()
    record = store.get(run_id)
    if record is None:
        return {"success": False, "error": f"Record not found: {run_id}"}
    return {"success": True, "record": record.to_dict()}

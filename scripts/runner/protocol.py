# -*- coding: utf-8 -*-
"""JSON-over-stdio communication protocol.

The Electron frontend launches Python scripts as child processes and
communicates via newline-delimited JSON on stdin/stdout.  This module
provides helpers for both sides of that protocol.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Optional


def read_stdin_json() -> dict[str, Any]:
    """Read a single JSON object from stdin and return it as a dict.

    Blocks until a complete line is available.  Returns an empty dict
    if stdin is closed or the payload is not valid JSON.
    """
    try:
        line = sys.stdin.readline()
        if not line:
            return {}
        return json.loads(line.strip())
    except (json.JSONDecodeError, EOFError, OSError):
        return {}


def emit(event: str, data: Optional[dict[str, Any]] = None) -> None:
    """Write a JSON event line to stdout for the Electron frontend.

    Parameters
    ----------
    event:
        Event type name (e.g. "step-start", "log", "result").
    data:
        Optional payload dictionary.
    """
    msg = {"event": event}
    if data:
        msg.update(data)
    try:
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    except (OSError, BrokenPipeError):
        pass


def emit_log(message: str, level: str = "info") -> None:
    """Convenience: emit a log event."""
    emit("log", {"level": level, "message": message})


def emit_error(message: str) -> None:
    """Convenience: emit an error event."""
    emit("error", {"message": message})


def emit_result(success: bool, data: Optional[dict[str, Any]] = None) -> None:
    """Convenience: emit a final result event."""
    payload = {"success": success}
    if data:
        payload.update(data)
    emit("result", payload)


def emit_step_start(step_name: str, step_index: int = 0) -> None:
    """Convenience: emit a step-start event."""
    emit("step-start", {"step": step_name, "index": step_index})


def emit_step_end(step_name: str, success: bool, message: str = "",
                  step_index: int = 0) -> None:
    """Convenience: emit a step-end event."""
    emit("step-end", {
        "step": step_name,
        "index": step_index,
        "success": success,
        "message": message,
    })

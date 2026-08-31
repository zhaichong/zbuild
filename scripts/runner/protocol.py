# -*- coding: utf-8 -*-
"""JSON-over-stdio communication protocol.

The Electron frontend launches Python scripts as child processes and
communicates via newline-delimited JSON on stdin/stdout.  This module
provides helpers for both sides of that protocol.
"""

import json
import sys
import threading
from typing import Any, Dict, Optional


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

# Serialize stdout writes so parallel project threads cannot interleave
# JSON event lines on the same stream.
_EMIT_LOCK = threading.Lock()


def read_stdin_json() -> Dict[str, Any]:
    """Read a JSON object from stdin and return it as a dict.

    Reads until EOF or newline to support both stream and single-shot payloads.
    Returns an empty dict if stdin is closed or the payload is not valid JSON.
    """
    try:
        stream = getattr(sys.stdin, "buffer", None)
        raw = stream.read().decode("utf-8-sig") if stream is not None else sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw.strip())
    except (json.JSONDecodeError, EOFError, OSError):
        return {}


def emit(event: Any, data: Optional[Dict[str, Any]] = None) -> None:
    """Write a JSON event line to stdout for the Electron frontend.

    Parameters
    ----------
    event:
        Event type name (e.g. "step-start", "log", "result") or a full event dict.
    data:
        Optional payload dictionary.
    """
    if isinstance(event, dict):
        msg = dict(event)
        if data:
            msg.update(data)
    else:
        msg = {"type": str(event)}
        if data:
            msg.update(data)
    try:
        with _EMIT_LOCK:
            sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    except (OSError, BrokenPipeError):
        pass


def emit_log(message: str, level: str = "info", project: str = "") -> None:
    """Convenience: emit a log event."""
    payload: Dict[str, Any] = {"level": level, "message": message}
    if project:
        payload["project"] = project
    emit("log", payload)


def emit_error(message: str, project: str = "") -> None:
    """Convenience: emit an error event."""
    payload: Dict[str, Any] = {"message": message}
    if project:
        payload["project"] = project
    emit("error", payload)


def emit_result(success: bool, data: Optional[Dict[str, Any]] = None) -> None:
    """Convenience: emit a final result event."""
    payload = {"success": success}
    if data:
        payload.update(data)
    emit("result", payload)


def emit_step_start(step_name: str, step_index: int = 0, project: str = "") -> None:
    """Convenience: emit a step-start event."""
    payload: Dict[str, Any] = {"step": step_name, "index": step_index}
    if project:
        payload["project"] = project
    emit("step-start", payload)


def emit_step_end(step_name: str, success: bool, message: str = "",
                  step_index: int = 0, project: str = "") -> None:
    """Convenience: emit a step-end event."""
    payload: Dict[str, Any] = {
        "step": step_name,
        "index": step_index,
        "success": success,
        "message": message,
    }
    if project:
        payload["project"] = project
    emit("step-end", payload)

# -*- coding: utf-8 -*-
"""Lightweight command registry and CLI dispatcher.

Commands are registered via the ``@register`` decorator and dispatched
by ``main()`` based on ``sys.argv[1]``.
"""

import json
from pathlib import Path
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional

# Ensure the scripts directory is in sys.path
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from runner.protocol import emit, emit_error, emit_result, read_stdin_json

# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

_COMMANDS: Dict[str, Callable[[Dict[str, Any]], Any]] = {}


def register(name: str) -> Callable:
    """Decorator that registers a function as a named CLI command.

    Usage::

        @register("detect-tools")
        def cmd_detect_tools(payload: dict) -> dict:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        _COMMANDS[name] = fn
        return fn
    return decorator


def get_command(name: str) ->Optional[Callable]:
    """Return the registered function for *name*, or None."""
    return _COMMANDS.get(name)


def list_commands() -> List[str]:
    """Return all registered command names."""
    return sorted(_COMMANDS.keys())


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: read command name from argv, payload from stdin, dispatch.

    Protocol
    --------
    1. ``sys.argv[1]`` is the command name.
    2. A single JSON object is read from stdin as the payload.
    3. The command function is called with the payload dict.
    4. The return value (a dict) is emitted as a ``result`` event.
    5. If the command raises, an ``error`` event is emitted.
    """
    if len(sys.argv) < 2:
        emit_error("No command specified. Available: " + ", ".join(list_commands()))
        sys.exit(1)

    command_name = sys.argv[1]
    fn = get_command(command_name)
    if fn is None:
        emit_error(f"Unknown command: {command_name}. Available: {', '.join(list_commands())}")
        sys.exit(1)

    # Read payload from stdin
    payload = read_stdin_json()

    # Apply configured git/bash/node paths before any command runs.
    # Electron often starts with a minimal PATH (no Git), which made
    # discover/refresh-branches return empty branch lists while still
    # finding repos via the filesystem.
    try:
        from tools.env_setup import apply_tools_env

        apply_tools_env(payload if isinstance(payload, dict) else {})
    except Exception:
        pass

    try:
        result = fn(payload)
        if isinstance(result, dict):
            emit_result(result.get("success", True), result)
        else:
            emit_result(True, {"data": result})
    except Exception as exc:
        tb = traceback.format_exc()
        emit_error(f"{type(exc).__name__}: {exc}")
        emit("log", {"level": "debug", "message": tb})
        emit_result(False, {"error": str(exc), "traceback": tb})
        sys.exit(1)

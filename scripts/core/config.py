# -*- coding: utf-8 -*-
"""Configuration loading, saving, and normalization.

Refactored from the original config.py to use centralized constants
and structured error handling.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from core.constants import (
    CONFIG_PATH,
    DEBUG_LOG_PATH,
    DATA_DIR,
    DEFAULT_BUILD_COMMAND,
    DEFAULT_BUILD_COMMANDS,
    DEFAULT_SERVER_UPLOAD_PATHS,
)
from core.errors import ConfigError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, *, default: Any = None) -> Any:
    """Load a JSON file, returning *default* if the file does not exist."""
    if not path.exists():
        return default if default is not None else {}
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(f"Failed to parse {path}: {exc}") from exc


def save_json(path: Path, data: Any) -> None:
    """Atomically write *data* as formatted JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(text, encoding="utf-8")
    try:
        tmp.replace(path)
    except PermissionError:
        path.write_text(text, encoding="utf-8")
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Debug logging
# ---------------------------------------------------------------------------

def write_debug(message: str, *args: Any) -> None:
    """Append a timestamped line to the debug log file."""
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{ts}] {message % args if args else message}\n"
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass  # debug logging must never crash the tool


# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

def default_config() -> dict[str, Any]:
    """Return a fresh default configuration dictionary."""
    return {
        "mode": "svn",
        "projects": [],
        "root_path": "",
        "svn_root": "https://10.1.1.120/svn/智慧病房特殊订单",
        "svn_credentials": {
            "username": "",
            "password": "",
        },
        "server": {
            "host": "",
            "port": 22,
            "username": "",
            "password": "",
        },
        "local_output": str(DATA_DIR / "local-output"),
        "auto_pull": True,
        "auto_install_deps": True,
        "skip_svn_commit": False,
        "node_required_version": "14.21.3",
        "build_command": DEFAULT_BUILD_COMMAND,
        "build_commands": dict(DEFAULT_BUILD_COMMANDS),
        "server_upload_paths": dict(DEFAULT_SERVER_UPLOAD_PATHS),
    }


# ---------------------------------------------------------------------------
# Config normalization
# ---------------------------------------------------------------------------

def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a configuration dictionary.

    Ensures all required keys exist with sane defaults and normalizes
    project entries.
    """
    defaults = default_config()
    config = {**defaults, **raw}

    # Ensure mode is valid
    if config["mode"] not in ("svn", "server", "local"):
        config["mode"] = "svn"

    # Normalize build_command (global fallback)
    raw_build_cmd = raw.get("build_command")
    if raw_build_cmd and isinstance(raw_build_cmd, str) and raw_build_cmd.strip():
        config["build_command"] = raw_build_cmd.strip()
    else:
        config["build_command"] = DEFAULT_BUILD_COMMAND

    # Normalize build_commands dict
    build_commands = config.get("build_commands")
    if not isinstance(build_commands, dict):
        config["build_commands"] = dict(DEFAULT_BUILD_COMMANDS)
    else:
        merged_cmds = dict(DEFAULT_BUILD_COMMANDS)
        merged_cmds.update({k: str(v).strip() for k, v in build_commands.items() if str(v).strip()})
        config["build_commands"] = merged_cmds

    # Normalize server_upload_paths dict
    server_paths = config.get("server_upload_paths")
    if not isinstance(server_paths, dict):
        config["server_upload_paths"] = dict(DEFAULT_SERVER_UPLOAD_PATHS)
    else:
        merged_paths = dict(DEFAULT_SERVER_UPLOAD_PATHS)
        merged_paths.update({k: str(v) for k, v in server_paths.items()})
        config["server_upload_paths"] = merged_paths

    # Normalize projects list
    projects = config.get("projects", [])
    if not isinstance(projects, list):
        config["projects"] = []
    else:
        normalized_projects = []
        for proj in projects:
            if isinstance(proj, str):
                normalized_projects.append({
                    "name": proj,
                    "path": "",
                    "branch": "",
                    "svn_leaf": proj,
                    "enabled": True,
                    "server_upload_path": config["server_upload_paths"].get(proj, ""),
                    "build_command": config["build_commands"].get(proj, config["build_command"]),
                })
            elif isinstance(proj, dict):
                p_name = proj.get("name", "")
                normalized_projects.append({
                    "name": p_name,
                    "path": proj.get("path", ""),
                    "branch": proj.get("branch", ""),
                    "svn_leaf": proj.get("svn_leaf", p_name),
                    "enabled": proj.get("enabled", True),
                    "server_upload_path": proj.get("server_upload_path") or config["server_upload_paths"].get(p_name, ""),
                    "build_command": proj.get("build_command") or config["build_commands"].get(p_name, config["build_command"]),
                })
        config["projects"] = normalized_projects

    # Ensure svn_credentials sub-dict
    if not isinstance(config.get("svn_credentials"), dict):
        config["svn_credentials"] = defaults.get("svn_credentials", {"username": "", "password": ""})

    # Ensure server sub-dict
    if not isinstance(config.get("server"), dict):
        config["server"] = defaults["server"]

    return config


# ---------------------------------------------------------------------------
# High-level config access
# ---------------------------------------------------------------------------

def load_config() -> dict[str, Any]:
    """Load the tool configuration, creating defaults if needed."""
    if not CONFIG_PATH.exists():
        cfg = default_config()
        save_json(CONFIG_PATH, cfg)
        return cfg
    raw = load_json(CONFIG_PATH, default={})
    return normalize_config(raw)


def save_config(config: dict[str, Any]) -> None:
    """Persist the configuration to disk."""
    save_json(CONFIG_PATH, config)

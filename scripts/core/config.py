# -*- coding: utf-8 -*-
"""Configuration loading, saving, and normalization.

Refactored from the original config.py to use centralized constants
and structured error handling.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

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

def default_config() -> Dict[str, Any]:
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
        "order_dir_path": "",
        "auto_pull": True,
        "auto_install_deps": True,
        "skip_svn_commit": False,
        "node_required_version": "14.21.3",
        "use_build_cache": True,
        "max_concurrent": 2,
        "build_command": DEFAULT_BUILD_COMMAND,
        "build_commands": dict(DEFAULT_BUILD_COMMANDS),
        "branch_build_commands": {},
        "artifact_paths": ["dist", "release", "build", "output", "target"],
        "project_artifact_paths": {},
        "project_svn_roots": {},
        "svn_upload_directory": "前端",
        "svn_locations": [],
        "server_upload_paths": dict(DEFAULT_SERVER_UPLOAD_PATHS),
    }


# ---------------------------------------------------------------------------
# Config normalization
# ---------------------------------------------------------------------------

def normalize_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a configuration dictionary.

    Ensures all required keys exist with sane defaults and normalizes
    project entries.
    """
    from git.build_cmd import resolve_branch_build_command

    defaults = default_config()
    config = dict(defaults)
    config.update(raw)

    # Ensure mode is valid
    if config["mode"] not in ("svn", "server", "local"):
        config["mode"] = "svn"

    # Normalize max_concurrent (parallel project workers, 1..8)
    try:
        config["max_concurrent"] = max(1, min(8, int(config.get("max_concurrent", 2) or 2)))
    except (TypeError, ValueError):
        config["max_concurrent"] = 2

    # Normalize svn_locations list
    raw_svn_locs = config.get("svn_locations")
    if isinstance(raw_svn_locs, list):
        config["svn_locations"] = raw_svn_locs
    else:
        config["svn_locations"] = []

    # Normalize order_dir_path
    raw_order_dir = raw.get("order_dir_path")
    if raw_order_dir and isinstance(raw_order_dir, str):
        config["order_dir_path"] = raw_order_dir.strip()
    else:
        config["order_dir_path"] = ""

    # Normalize project_svn_roots dict
    proj_svn_roots = config.get("project_svn_roots")
    if not isinstance(proj_svn_roots, dict):
        config["project_svn_roots"] = {}
    else:
        config["project_svn_roots"] = {
            k: str(v).strip() for k, v in proj_svn_roots.items() if str(v).strip()
        }

    raw_upload_directory = raw.get("svn_upload_directory", config.get("svn_upload_directory"))
    config["svn_upload_directory"] = str(raw_upload_directory or "").strip()

    # Normalize build_command (global fallback)
    raw_build_cmd = raw.get("build_command")
    if isinstance(raw_build_cmd, str) and raw_build_cmd.strip():
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

    # Normalize branch_build_commands dict
    raw_branch_cmds = config.get("branch_build_commands")
    if not isinstance(raw_branch_cmds, dict):
        config["branch_build_commands"] = {}
    else:
        norm_branch_cmds = {}
        for p_name, b_map in raw_branch_cmds.items():
            if isinstance(b_map, dict):
                norm_branch_cmds[str(p_name)] = {
                    str(b): str(cmd).strip() for b, cmd in b_map.items() if str(cmd).strip()
                }
        config["branch_build_commands"] = norm_branch_cmds

    # Normalize artifact_paths list
    raw_art_paths = config.get("artifact_paths")
    default_art_paths = ["dist", "release", "build", "output", "target"]
    if isinstance(raw_art_paths, str):
        config["artifact_paths"] = [p.strip() for p in raw_art_paths.replace(";", ",").split(",") if p.strip()]
    elif isinstance(raw_art_paths, list):
        art_list = []
        for p in raw_art_paths:
            if isinstance(p, str):
                art_list.extend([s.strip() for s in p.replace(";", ",").split(",") if s.strip()])
            elif p:
                art_list.append(str(p).strip())
        config["artifact_paths"] = art_list
    else:
        config["artifact_paths"] = default_art_paths
    if not config["artifact_paths"]:
        config["artifact_paths"] = default_art_paths

    # Normalize project_artifact_paths dict
    proj_art_paths = config.get("project_artifact_paths")
    if not isinstance(proj_art_paths, dict):
        config["project_artifact_paths"] = {}
    else:
        config["project_artifact_paths"] = {
            k: (str(v).strip() if isinstance(v, str) else ", ".join(v) if isinstance(v, list) else str(v))
            for k, v in proj_art_paths.items()
            if v
        }

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
                    "svn_root": config["project_svn_roots"].get(proj, config["svn_root"]),
                    "enabled": True,
                    "server_upload_path": config["server_upload_paths"].get(proj, ""),
                    "build_command": resolve_branch_build_command(config, proj, ""),
                })
            elif isinstance(proj, dict):
                p_name = proj.get("name", "")
                p_branch = proj.get("branch", "")
                normalized_projects.append({
                    "name": p_name,
                    "path": proj.get("path", ""),
                    "branch": p_branch,
                    "svn_leaf": proj.get("svn_leaf", p_name),
                    "svn_root": proj.get("svn_root") or config["project_svn_roots"].get(p_name, config["svn_root"]),
                    "enabled": proj.get("enabled", True),
                    "server_upload_path": proj.get("server_upload_path") or config["server_upload_paths"].get(p_name, ""),
                    "build_command": proj.get("build_command") or resolve_branch_build_command(config, p_name, p_branch),
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

def load_config() -> Dict[str, Any]:
    """Load the tool configuration, creating defaults if needed."""
    if not CONFIG_PATH.exists():
        cfg = default_config()
        save_json(CONFIG_PATH, cfg)
        return cfg
    raw = load_json(CONFIG_PATH, default={})
    return normalize_config(raw)


def save_config(config: Dict[str, Any]) -> None:
    """Persist the configuration to disk."""
    save_json(CONFIG_PATH, config)

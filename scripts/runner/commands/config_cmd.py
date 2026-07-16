# -*- coding: utf-8 -*-
"""Commands: config, save-config."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from core.config import load_config, save_config, default_config


@register("config")
def cmd_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the current configuration."""
    config = load_config()
    return {"success": True, "config": config}


@register("save-config")
def cmd_save_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Save the provided configuration to disk."""
    config_data = payload.get("config")
    if not config_data or not isinstance(config_data, dict):
        return {"success": False, "error": "Missing or invalid 'config' in payload"}
    save_config(config_data)
    return {"success": True, "message": "Configuration saved"}

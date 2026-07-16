# -*- coding: utf-8 -*-
"""Commands: template-list, template-get, template-save, template-delete."""
from __future__ import annotations

from typing import Any

from runner.cli import register
from core.templates import TemplateStore
from core.models import TaskTemplate


@register("template-list")
def cmd_template_list(payload: dict[str, Any]) -> dict[str, Any]:
    """List all saved task templates."""
    store = TemplateStore()
    templates = store.list()
    return {
        "success": True,
        "templates": [t.to_dict() for t in templates],
    }


@register("template-get")
def cmd_template_get(payload: dict[str, Any]) -> dict[str, Any]:
    """Get a single template by ID."""
    template_id = payload.get("template_id", "")
    if not template_id:
        return {"success": False, "error": "Missing 'template_id'"}

    store = TemplateStore()
    template = store.get(template_id)
    if template is None:
        return {"success": False, "error": f"Template not found: {template_id}"}
    return {"success": True, "template": template.to_dict()}


@register("template-save")
def cmd_template_save(payload: dict[str, Any]) -> dict[str, Any]:
    """Save a new template or update an existing one."""
    name = payload.get("name", "")
    if not name:
        return {"success": False, "error": "Missing 'name'"}

    config = payload.get("config", {})
    mode = payload.get("mode", "svn")
    description = payload.get("description", "")
    template_id = payload.get("template_id", "")

    store = TemplateStore()

    if template_id:
        # Update existing
        template = store.get(template_id)
        if template:
            template.name = name
            template.config = config
            template.mode = mode
            template.description = description
            store.update(template)
            return {"success": True, "template": template.to_dict(), "message": "Template updated"}

    # Create new
    template = TaskTemplate.from_current_config(
        template_id="",
        name=name,
        config=config,
        mode=mode,
        description=description,
    )
    store.create(template)
    return {"success": True, "template": template.to_dict(), "message": "Template saved"}


@register("template-delete")
def cmd_template_delete(payload: dict[str, Any]) -> dict[str, Any]:
    """Delete a template by ID."""
    template_id = payload.get("template_id", "")
    if not template_id:
        return {"success": False, "error": "Missing 'template_id'"}

    store = TemplateStore()
    deleted = store.delete(template_id)
    if not deleted:
        return {"success": False, "error": f"Template not found: {template_id}"}
    return {"success": True, "message": "Template deleted"}

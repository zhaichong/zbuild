# -*- coding: utf-8 -*-
"""Commands: template-list, template-get, template-save, template-delete."""

from typing import Any, Dict

from runner.cli import register
from core.templates import TemplateStore
from core.models import TaskTemplate
from core.secrets import without_secrets


@register("template-list")
def cmd_template_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List all saved task templates."""
    store = TemplateStore()
    templates = store.list()
    return {
        "success": True,
        "templates": [t.to_dict() for t in templates],
    }


@register("template-get")
def cmd_template_get(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Get a single template by ID."""
    template_id = payload.get("id", "")
    if not template_id:
        return {"success": False, "error": "Missing 'id'"}

    store = TemplateStore()
    template = store.get(template_id)
    if template is None:
        return {"success": False, "error": f"Template not found: {template_id}"}
    return {"success": True, "template": template.to_dict()}


@register("template-save")
def cmd_template_save(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Save a new template or update an existing one.

    Passwords and other secrets are stripped before persistence so templates
    never become a secondary credential store.
    """
    name = payload.get("name", "")
    if not name:
        return {"success": False, "error": "Missing 'name'"}

    config = without_secrets(payload.get("config", {}) or {})
    mode = payload.get("mode", "svn")
    description = payload.get("description", "")
    template_id = payload.get("id", "")

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
def cmd_template_delete(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a template by ID."""
    template_id = payload.get("id", "")
    if not template_id:
        return {"success": False, "error": "Missing 'id'"}

    store = TemplateStore()
    deleted = store.delete(template_id)
    if not deleted:
        return {"success": False, "error": f"Template not found: {template_id}"}
    return {"success": True, "message": "Template deleted"}

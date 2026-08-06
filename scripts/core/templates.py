# -*- coding: utf-8 -*-
"""Task template store.

CRUD operations for TaskTemplate JSON files stored in TEMPLATES_DIR.
Templates allow users to save and reuse pipeline configurations.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.constants import TEMPLATES_DIR
from core.models import TaskTemplate
from core.secrets import without_secrets


def _template_payload(template: TaskTemplate) -> Dict[str, Any]:
    """Serialize a template with credentials stripped from config."""
    data = template.to_dict()
    if isinstance(data.get("config"), dict):
        data["config"] = without_secrets(data["config"])
    return data


class TemplateStore:
    """Manage reusable task templates on disk.

    Each template is stored as ``{TEMPLATES_DIR}/{template_id}.json``.
    """

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, template: TaskTemplate) -> str:
        """Save a new template. Returns the template_id."""
        if not template.template_id:
            template.template_id = uuid.uuid4().hex[:12]
        if not template.created_at:
            now = time.time()
            template.created_at = now
            template.updated_at = now

        # Keep in-memory template free of secrets so callers never re-save them.
        if isinstance(template.config, dict):
            template.config = without_secrets(template.config)
        path = self.templates_dir / f"{template.template_id}.json"
        path.write_text(
            json.dumps(_template_payload(template), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return template.template_id

    def get(self, template_id: str) -> Optional[TaskTemplate]:
        """Load a single template by ID."""
        path = self.templates_dir / f"{template_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            tpl = TaskTemplate.from_dict(data)
            if isinstance(tpl.config, dict):
                tpl.config = without_secrets(tpl.config)
            return tpl
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def list(self) -> List[TaskTemplate]:
        """Return all templates, sorted by creation time (newest first)."""
        templates: List[TaskTemplate] = []
        for path in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                tpl = TaskTemplate.from_dict(data)
                if isinstance(tpl.config, dict):
                    tpl.config = without_secrets(tpl.config)
                templates.append(tpl)
            except (json.JSONDecodeError, KeyError, OSError):
                continue
        templates.sort(key=lambda t: t.created_at, reverse=True)
        return templates

    def update(self, template: TaskTemplate) -> bool:
        """Update an existing template. Returns True if it existed."""
        path = self.templates_dir / f"{template.template_id}.json"
        if not path.exists():
            return False
        template.updated_at = time.time()
        if isinstance(template.config, dict):
            template.config = without_secrets(template.config)
        path.write_text(
            json.dumps(_template_payload(template), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True

    def delete(self, template_id: str) -> bool:
        """Delete a template by ID. Returns True if it existed."""
        path = self.templates_dir / f"{template_id}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    @classmethod
    def from_current_config(cls, name: str, config: Dict[str, Any],
                            mode: str = "svn", description: str = "",
                            templates_dir: Optional[Path] = None) -> TaskTemplate:
        """Create a template from the current configuration and save it."""
        store = cls(templates_dir)
        template = TaskTemplate.from_current_config(
            template_id="",
            name=name,
            config=config,
            mode=mode,
            description=description,
        )
        store.create(template)
        return template

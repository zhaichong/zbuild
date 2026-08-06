# -*- coding: utf-8 -*-
"""Command: run - delegates to the Pipeline."""

from typing import Any, Dict

from runner.cli import register
from runner.protocol import emit, emit_log, emit_result


@register("run")
def cmd_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the full build-and-upload pipeline.

    The payload contains the complete configuration for this run,
    including mode, projects, and upload settings.
    """
    from workflow.pipeline import Pipeline

    try:
        pipeline = Pipeline(payload)
        record = pipeline.run()
        return {
            "success": record.success,
            "run_id": record.run_id,
            "projects": [p.to_dict() for p in record.projects],
        }
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        emit_log(f"Pipeline error: {exc}", level="error")
        emit_log(tb, level="debug")
        return {"success": False, "error": str(exc)}

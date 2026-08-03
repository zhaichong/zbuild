# -*- coding: utf-8 -*-
"""Command: create-order-dir - creates order output folder and Excel form."""
from __future__ import annotations

from typing import Any

from runner.cli import register


@register("create-order-dir")
def cmd_create_order_dir(payload: dict[str, Any]) -> dict[str, Any]:
    """Create the order directory and Excel test submission form.

    Payload options:
      order_dir_base: Base directory path (e.g. D:\\yh\\特殊订单\\2026)
      order_no: Order number (e.g. 2026-1396)
      hospital_name: Hospital name (e.g. 广州中医药大学顺德医院)
      projects: List of selected projects
    """
    from tools.order_dir import create_order_directory

    config = payload.get("config", {})
    form = config.get("form", {})

    order_dir_base = payload.get("order_dir_base") or config.get("order_dir_path") or ""
    order_no = payload.get("order_no") or config.get("order_no") or form.get("orderNo") or form.get("order_no") or ""
    hospital_name = payload.get("hospital_name") or config.get("hospital_name") or form.get("hospitalName") or form.get("hospital_name") or ""
    projects = payload.get("projects") or config.get("projects") or []

    return create_order_directory(
        order_dir_base=order_dir_base,
        order_no=str(order_no),
        hospital_name=str(hospital_name),
        projects=projects,
    )

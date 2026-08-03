# -*- coding: utf-8 -*-
"""Utility for creating order output directories and Excel test submission forms based on the official template.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def find_template_file(order_dir_base: str | Path | None = None) -> Optional[Path]:
    """Find the official 提测单 .xlsx template file."""
    # 1. Check local references directory inside zbuild
    pkg_dir = Path(__file__).resolve().parents[2]
    bundled_tmpl = pkg_dir / "references" / "template_test_order.xlsx"
    if bundled_tmpl.exists():
        return bundled_tmpl

    # Also check relative to scripts
    scripts_dir = Path(__file__).resolve().parents[1]
    bundled_tmpl2 = scripts_dir / "references" / "template_test_order.xlsx"
    if bundled_tmpl2.exists():
        return bundled_tmpl2

    # 2. Check in order_dir_base if provided
    if order_dir_base:
        base = Path(order_dir_base)
        if base.exists():
            ref = base / "2026-1319 -深圳市新华医院" / "2026-1319 -深圳市新华医院医院提测单.xlsx"
            if ref.exists():
                return ref
            # Search for any reference excel ending in 提测单.xlsx
            matches = list(base.rglob("*提测单.xlsx"))
            if matches:
                return matches[0]

    return None


def create_order_directory(
    order_dir_base: str | Path,
    order_no: str,
    hospital_name: str,
    projects: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create the order directory and test submission Excel file (.xlsx) by filling in the official template.

    Naming rule:
      Folder: {order_dir_base}/{order_no}-{hospital_name}
      Excel:  {folder_name}医院提测单.xlsx
    """
    if not order_dir_base:
        return {"success": False, "message": "未配置提测目录根路径"}
    if not order_no or not hospital_name:
        return {"success": False, "message": "订单号和医院名称不能为空"}

    base_path = Path(order_dir_base)
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"success": False, "message": f"创建基础目录失败: {e}"}

    clean_order = str(order_no).strip()
    clean_hosp = str(hospital_name).strip()

    folder_name = f"{clean_order}-{clean_hosp}"
    target_dir = base_path / folder_name

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"success": False, "message": f"创建订单目录失败 [{target_dir}]: {e}"}

    excel_name = f"{folder_name}医院提测单.xlsx"
    excel_path = target_dir / excel_name

    excel_created = False
    try:
        tmpl_path = find_template_file(order_dir_base)
        if tmpl_path and tmpl_path.exists():
            _fill_excel_template(tmpl_path, excel_path, folder_name, projects or [])
            excel_created = True
        else:
            _generate_fallback_excel(excel_path, folder_name, projects or [])
            excel_created = True
    except Exception as e:
        logger.warning(f"生成 Excel 提测单失败: {e}")

    return {
        "success": True,
        "dir": str(target_dir),
        "excel": str(excel_path),
        "excel_created": excel_created,
        "message": f"成功创建目录: {target_dir}（包含文件: {excel_name}）",
    }


def _fill_excel_template(
    tmpl_path: Path,
    output_path: Path,
    folder_name: str,
    projects: list[dict[str, Any]],
) -> None:
    """Load the official template file and fill in B6 (folder name) and B12 (changed projects)."""
    import openpyxl

    wb = openpyxl.load_workbook(tmpl_path)

    # Locate worksheet (usually sheet named '测试单' or second worksheet)
    ws = None
    for sheet in wb.worksheets:
        if "测试" in sheet.title or sheet.title != "Export Summary":
            ws = sheet
            break

    if not ws:
        ws = wb.active

    # B6: 产品名称/特殊订单编号
    ws["B6"] = folder_name

    # B12: 产品主要更改项目
    lines = []
    if projects:
        for idx, p in enumerate(projects, start=1):
            p_name = p.get("name") or p.get("projectName") or ""
            p_branch = p.get("branch") or p.get("currentBranch") or ""
            if p_branch:
                lines.append(f"{idx}、{p_name} ({p_branch})")
            else:
                lines.append(f"{idx}、{p_name}")
    else:
        lines.append("1、特殊订单需求更新")

    ws["B12"] = "\n".join(lines)

    wb.save(output_path)


def _generate_fallback_excel(
    filepath: Path,
    folder_name: str,
    projects: list[dict[str, Any]],
) -> None:
    """Fallback generator if template is missing."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        filepath.touch(exist_ok=True)
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "测试单"

    ws["A2"] = "山东亚华电子股份有限公司"
    ws["A3"] = "测试单"
    ws["A4"] = "编号：YH/D-B04-01-F002                               "
    ws["C4"] = "版本：V1.0     "
    ws["E4"] = "   NO:"
    ws["A5"] = "基本信息"
    ws["A6"] = "产品名称/特殊订单编号"
    ws["B6"] = folder_name
    ws["A7"] = "测试类型/阶段"
    ws["B7"] = "特殊订单"
    ws["A8"] = "产品型号"
    ws["B8"] = "主机：           A10"
    ws["A9"] = "产品版本"
    ws["B9"] = "操作系统:"
    ws["A10"] = "是否需要小批量试制（必选）"
    ws["B10"] = "■不需要            □需要"
    ws["A11"] = "产品主要更改项目"

    lines = []
    if projects:
        for idx, p in enumerate(projects, start=1):
            p_name = p.get("name") or p.get("projectName") or ""
            p_branch = p.get("branch") or p.get("currentBranch") or ""
            lines.append(f"{idx}、{p_name} ({p_branch})" if p_branch else f"{idx}、{p_name}")
    else:
        lines.append("1、特殊订单需求更新")

    ws["A12"] = 1
    ws["B12"] = "\n".join(lines)

    wb.save(filepath)

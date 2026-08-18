# -*- coding: utf-8 -*-
"""Command: order-deploy-list and order-deploy-run."""

from typing import Any, Dict
from runner.cli import register
from workflow.order_deploy import list_svn_order_tree, deploy_order_packages, export_svn_file_for_preview


@register("order-deploy-list")
def cmd_order_deploy_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively list contents of an SVN order directory and build a tree."""
    svn_url = payload.get("svnUrl") or payload.get("url") or ""
    svn_exe = payload.get("svn") or payload.get("svn_exe") or "svn"
    username = payload.get("svnUsername") or payload.get("username") or ""
    password = payload.get("svnPassword") or payload.get("password") or ""
    server_upload_paths = payload.get("serverUploadPaths") or {}

    if not svn_url:
        return {"success": False, "error": "缺少 SVN 订单路径 (svnUrl)"}

    return list_svn_order_tree(
        svn_url=svn_url,
        svn_exe=svn_exe,
        username=username,
        password=password,
        server_upload_paths=server_upload_paths,
    )


@register("order-deploy-run")
def cmd_order_deploy_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute order frontend packages deployment to remote server."""
    return deploy_order_packages(payload)


@register("order-deploy-open-file")
def cmd_order_deploy_open_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Export a single file from SVN and return local temp path for previewing."""
    file_url = payload.get("fileUrl") or payload.get("url") or ""
    svn_exe = payload.get("svn") or payload.get("svn_exe") or "svn"
    username = payload.get("svnUsername") or payload.get("username") or ""
    password = payload.get("svnPassword") or payload.get("password") or ""

    if not file_url:
        return {"success": False, "error": "缺少文件 SVN 路径 (fileUrl)"}

    return export_svn_file_for_preview(
        file_url=file_url,
        svn_exe=svn_exe,
        username=username,
        password=password,
    )


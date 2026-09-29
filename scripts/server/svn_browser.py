# -*- coding: utf-8 -*-
"""SVN repository browser and APK exporter."""

import asyncio
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from tools.exec import run_process
from uploaders.svn import convert_visualsvn_url, join_svn_url, svn_args

logger = logging.getLogger(__name__)


def _format_bytes(size: Optional[int]) -> str:
    """Format byte count into human-readable string."""
    if size is None or size < 0:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def _format_svn_error(raw_err: str) -> str:
    """Format raw SVN CLI error into clear, actionable message."""
    err = (raw_err or "").strip()
    if not err:
        return "SVN 操作失败"
    if "Authentication failed" in err or "E215004" in err:
        return f"SVN 认证失败: 账号或密码错误，请在设置中配置正确的 SVN 凭据 ({err})"
    if "E170013" in err:
        return f"无法连接到 SVN 仓库: 请检查网络连接或仓库地址是否正确 ({err})"
    if "E195019" in err:
        return f"SVN 路径不是有效的仓库地址: 请检查是否误复制了网页预览链接或路径不完整 ({err})"
    return err


def normalize_svn_url(url: str) -> str:
    """Normalize an SVN URL by converting VisualSVN URLs, decoding redundant quotes and trailing slashes."""
    if not url:
        return ""
    converted = convert_visualsvn_url(url)
    text = unquote(str(converted)).strip().replace("\\", "/").rstrip("/")
    if "://" in text:
        scheme, rest = text.split("://", 1)
        parts = [p for p in rest.split("/") if p]
        return f"{scheme}://" + "/".join(parts)
    return text


def _build_target_url(base_url: str, subpath: str = "") -> str:
    base_clean = convert_visualsvn_url(base_url)
    subpath_clean = subpath.strip().replace("\\", "/").strip("/")
    if not subpath_clean:
        try:
            return join_svn_url(base_clean)
        except Exception:
            return base_clean.rstrip("/")
    segments = [s for s in subpath_clean.split("/") if s]
    try:
        return join_svn_url(base_clean, *segments)
    except Exception:
        return base_clean.rstrip("/") + "/" + "/".join(segments)


async def browse_directory(
    base_url: str,
    subpath: str = "",
    username: str = "",
    password: str = "",
    svn_bin: str = "svn",
) -> Dict[str, Any]:
    """Browse a single directory in SVN repository."""
    exe = svn_bin or "svn"
    target_url = _build_target_url(base_url, subpath)
    auth = svn_args(username, password)
    clean_subpath = subpath.strip().replace("\\", "/").strip("/")

    def _sync_browse() -> Dict[str, Any]:
        cmd = [exe, "list", "--xml", target_url, *auth]
        proc = run_process(cmd, timeout=30)
        directories: List[Dict[str, Any]] = []
        apks: List[Dict[str, Any]] = []
        other_files: List[Dict[str, Any]] = []

        if proc.returncode == 0 and proc.stdout.strip():
            try:
                root = ET.fromstring(proc.stdout)
                for entry in root.findall(".//entry"):
                    kind = entry.get("kind", "file")
                    name_elem = entry.find("name")
                    if name_elem is None or not name_elem.text:
                        continue
                    item_name = name_elem.text.strip()
                    size_elem = entry.find("size")
                    size = (
                        int(size_elem.text)
                        if (size_elem is not None and size_elem.text and size_elem.text.isdigit())
                        else None
                    )

                    commit_elem = entry.find("commit")
                    revision = commit_elem.get("revision", "") if commit_elem is not None else ""
                    date_elem = commit_elem.find("date") if commit_elem is not None else None
                    date = date_elem.text if date_elem is not None and date_elem.text else ""
                    author_elem = commit_elem.find("author") if commit_elem is not None else None
                    author = author_elem.text if author_elem is not None and author_elem.text else ""

                    rel_path = f"{clean_subpath}/{item_name}".strip("/") if clean_subpath else item_name
                    item_data = {
                        "name": item_name,
                        "path": rel_path,
                        "fullUrl": _build_target_url(target_url, item_name),
                        "size": size,
                        "sizeDisplay": _format_bytes(size),
                        "kind": kind,
                        "revision": revision,
                        "date": date,
                        "author": author,
                    }

                    if kind == "dir":
                        directories.append(item_data)
                    elif item_name.lower().endswith(".apk"):
                        apks.append(item_data)
                    else:
                        other_files.append(item_data)

                directories.sort(key=lambda x: x["name"].lower())
                apks.sort(key=lambda x: x["name"].lower())
                other_files.sort(key=lambda x: x["name"].lower())

                return {
                    "success": True,
                    "currentPath": clean_subpath,
                    "fullUrl": target_url,
                    "directories": directories,
                    "apks": apks,
                    "otherFiles": other_files,
                    "totalApks": len(apks),
                }
            except Exception as ex:
                logger.warning("Failed to parse svn list XML: %s", ex)

        # Fallback to plain svn list
        plain_cmd = [exe, "list", target_url, *auth]
        plain_proc = run_process(plain_cmd, timeout=30)
        if plain_proc.returncode == 0 and plain_proc.stdout.strip():
            for line in plain_proc.stdout.strip().splitlines():
                raw = line.strip()
                if not raw:
                    continue
                is_dir = raw.endswith("/")
                item_name = raw.rstrip("/")
                rel_path = f"{clean_subpath}/{item_name}".strip("/") if clean_subpath else item_name
                item_data = {
                    "name": item_name,
                    "path": rel_path,
                    "fullUrl": _build_target_url(target_url, item_name),
                    "size": None,
                    "sizeDisplay": "",
                    "kind": "dir" if is_dir else "file",
                }
                if is_dir:
                    directories.append(item_data)
                elif item_name.lower().endswith(".apk"):
                    apks.append(item_data)
                else:
                    other_files.append(item_data)

            directories.sort(key=lambda x: x["name"].lower())
            apks.sort(key=lambda x: x["name"].lower())
            other_files.sort(key=lambda x: x["name"].lower())

            return {
                "success": True,
                "currentPath": clean_subpath,
                "fullUrl": target_url,
                "directories": directories,
                "apks": apks,
                "otherFiles": other_files,
                "totalApks": len(apks),
            }

        err = proc.stderr.strip() or plain_proc.stderr.strip() or f"SVN list 失败 (退出码: {proc.returncode})"
        return {
            "success": False,
            "error": _format_svn_error(err),
            "currentPath": clean_subpath,
            "fullUrl": target_url,
            "directories": [],
            "apks": [],
            "otherFiles": [],
            "totalApks": 0,
        }

    return await asyncio.to_thread(_sync_browse)


async def search_apks_recursive(
    base_url: str,
    subpath: str = "",
    keyword: str = "",
    username: str = "",
    password: str = "",
    svn_bin: str = "svn",
) -> Dict[str, Any]:
    """Search for APK files recursively in SVN."""
    exe = svn_bin or "svn"
    target_url = _build_target_url(base_url, subpath)
    auth = svn_args(username, password)
    clean_subpath = subpath.strip().replace("\\", "/").strip("/")
    kw = (keyword or "").strip().lower()

    def _sync_search() -> Dict[str, Any]:
        cmd = [exe, "list", "-R", "--xml", target_url, *auth]
        proc = run_process(cmd, timeout=60)
        apks: List[Dict[str, Any]] = []

        if proc.returncode == 0 and proc.stdout.strip():
            try:
                root = ET.fromstring(proc.stdout)
                for entry in root.findall(".//entry"):
                    kind = entry.get("kind", "file")
                    if kind != "file":
                        continue
                    name_elem = entry.find("name")
                    if name_elem is None or not name_elem.text:
                        continue
                    rel_path = name_elem.text.replace("\\", "/").strip("/")
                    item_name = PurePosixPath(rel_path).name
                    if not item_name.lower().endswith(".apk"):
                        continue
                    if kw and kw not in item_name.lower() and kw not in rel_path.lower():
                        continue

                    size_elem = entry.find("size")
                    size = (
                        int(size_elem.text)
                        if (size_elem is not None and size_elem.text and size_elem.text.isdigit())
                        else None
                    )

                    commit_elem = entry.find("commit")
                    revision = commit_elem.get("revision", "") if commit_elem is not None else ""
                    date_elem = commit_elem.find("date") if commit_elem is not None else None
                    date = date_elem.text if date_elem is not None and date_elem.text else ""
                    author_elem = commit_elem.find("author") if commit_elem is not None else None
                    author = author_elem.text if author_elem is not None and author_elem.text else ""

                    full_rel = f"{clean_subpath}/{rel_path}".strip("/") if clean_subpath else rel_path
                    apks.append({
                        "name": item_name,
                        "path": full_rel,
                        "fullUrl": _build_target_url(target_url, rel_path),
                        "size": size,
                        "sizeDisplay": _format_bytes(size),
                        "revision": revision,
                        "date": date,
                        "author": author,
                    })

                apks.sort(key=lambda x: x["name"].lower())
                return {
                    "success": True,
                    "apks": apks,
                    "count": len(apks),
                }
            except Exception as ex:
                logger.warning("Failed to parse recursive svn list XML: %s", ex)

        # Fallback to plain list -R
        plain_cmd = [exe, "list", "-R", target_url, *auth]
        plain_proc = run_process(plain_cmd, timeout=60)
        if plain_proc.returncode == 0 and plain_proc.stdout.strip():
            for line in plain_proc.stdout.strip().splitlines():
                raw = line.strip()
                if not raw or raw.endswith("/"):
                    continue
                rel_path = raw.replace("\\", "/").strip("/")
                item_name = PurePosixPath(rel_path).name
                if not item_name.lower().endswith(".apk"):
                    continue
                if kw and kw not in item_name.lower() and kw not in rel_path.lower():
                    continue

                full_rel = f"{clean_subpath}/{rel_path}".strip("/") if clean_subpath else rel_path
                apks.append({
                    "name": item_name,
                    "path": full_rel,
                    "fullUrl": _build_target_url(target_url, rel_path),
                    "size": None,
                    "sizeDisplay": "",
                })

            apks.sort(key=lambda x: x["name"].lower())
            return {
                "success": True,
                "apks": apks,
                "count": len(apks),
            }

        err = proc.stderr.strip() or plain_proc.stderr.strip() or f"SVN list -R 失败 (退出码: {proc.returncode})"
        return {
            "success": False,
            "error": _format_svn_error(err),
            "apks": [],
            "count": 0,
        }

    return await asyncio.to_thread(_sync_search)


async def export_single_apk(
    base_url: str,
    apk_remote_path: str,
    target_cache_dir: str,
    username: str = "",
    password: str = "",
    svn_bin: str = "svn",
) -> Dict[str, Any]:
    """Export a single APK from SVN into target cache directory."""
    exe = svn_bin or "svn"
    auth = svn_args(username, password)
    clean_path = apk_remote_path.strip().replace("\\", "/").strip("/")
    filename = PurePosixPath(clean_path).name

    if clean_path.startswith(("http://", "https://", "svn://")):
        file_url = clean_path
    else:
        file_url = _build_target_url(base_url, clean_path)

    def _sync_export() -> Dict[str, Any]:
        os.makedirs(target_cache_dir, exist_ok=True)
        dest_file = Path(target_cache_dir) / filename

        cmd = [exe, "export", "--force", file_url, str(dest_file), *auth]
        proc = run_process(cmd, timeout=180)
        if proc.returncode == 0 and dest_file.exists():
            size = dest_file.stat().st_size
            return {
                "success": True,
                "localPath": str(dest_file.resolve()),
                "filename": filename,
                "size": size,
                "sizeDisplay": _format_bytes(size),
            }
        err = proc.stderr.strip() or proc.stdout.strip() or f"导出失败 (退出码: {proc.returncode})"
        return {
            "success": False,
            "error": _format_svn_error(err),
        }

    return await asyncio.to_thread(_sync_export)

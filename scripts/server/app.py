# -*- coding: utf-8 -*-
"""aiohttp Web and WebSocket Application for zbuild."""

import asyncio
import json
import logging
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote

import aiohttp
from aiohttp import web

# Ensure the scripts directory is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.runner_service import runner_service
from server.db_service import test_db_connection, execute_db_sql
from server.config_service import ConfigConflict, WebConfigService
from server.profile_store import ProfileConflict, ProfileStore
from server.security import PinnedResolver, assert_origin_allowed, resolve_safe_proxy_target
from server.task_manager import TaskManager
from server.task_store import TaskStore
from server.task_routes import register_task_routes
from server.workspace import WorkspaceManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("zbuild-server")

PROFILE_COOKIE = "zbuild_profile"
PROFILE_CONFIG_KEYS = (
    "selected_projects", "project_branches", "hospital_name", "order_no",
    "order_notes", "create_order_dir", "svn_credentials", "svn_upload_directory",
    "artifact_paths", "project_artifact_paths",
)


def _profile_id(value: object) -> str:
    value = str(value or "")
    return value if len(value) == 32 and all(char in "0123456789abcdef" for char in value) else uuid.uuid4().hex


def _personal_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Only values that are safe and useful to remember per browser."""
    result = {key: config.get(key) for key in PROFILE_CONFIG_KEYS if key in config}
    credentials = result.get("svn_credentials")
    if isinstance(credentials, dict):
        result["svn_credentials"] = {
            "username": credentials.get("username", ""),
            "password": credentials.get("password", ""),
        }
    return result


def _execution_config(system_config: Dict[str, Any], profile_config: Dict[str, Any]) -> Dict[str, Any]:
    """Build execution input without allowing browsers to replace server settings."""
    value = json.loads(json.dumps(system_config))
    # Credentials in the old shared config must never silently become another
    # browser's identity after profiles are enabled.
    value.pop("svn_credentials", None)
    for key in PROFILE_CONFIG_KEYS:
        if key in profile_config:
            value[key] = profile_config[key]
    return value


def _config_view(system_public: Dict[str, Any], profile_public: Dict[str, Any]) -> Dict[str, Any]:
    value = json.loads(json.dumps(system_public.get("config") or {}))
    # Credentials and current form data must not inherit an old shared Web
    # configuration. Artifact-directory defaults may inherit until this browser
    # saves its own choice.
    for key in PROFILE_CONFIG_KEYS:
        if key in {"artifact_paths", "project_artifact_paths", "svn_upload_directory"}:
            continue
        value.pop(key, None)
    value.update(profile_public.get("config") or {})
    status = dict(system_public.get("secretStatus") or {})
    status["svnPassword"] = bool((profile_public.get("secretStatus") or {}).get("svnPassword"))
    return {"config": value, "revision": profile_public.get("revision", "0"), "secretStatus": status}


def _assert_allowed_svn_url(url: object, execution_config: Dict[str, Any]) -> None:
    """Only permit SVN endpoints administered in the server configuration."""
    candidate = unquote(str(url or "")).rstrip("/")
    roots = [execution_config.get("svn_root", "")]
    roots.extend(
        item.get("url", "") for item in execution_config.get("svn_locations", [])
        if isinstance(item, dict)
    )
    roots.extend((execution_config.get("project_svn_roots") or {}).values())
    for root in roots:
        normalized = unquote(str(root or "")).rstrip("/")
        if normalized and (candidate == normalized or candidate.startswith(normalized + "/")):
            return
    raise ValueError("SVN 地址不在服务端配置的目录范围内")


# ---------------------------------------------------------------------------
# Config Format Converters (Python snake_case <-> Frontend camelCase)
# ---------------------------------------------------------------------------

def py_config_to_frontend(py: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(py, dict):
        py = {}
    server = py.get("server") or {}
    svn_creds = py.get("svn_credentials") or {}
    tools = py.get("tools") or {}
    return {
        "rootPath": py.get("root_path", ""),
        "svnRootUrl": py.get("svn_root", ""),
        "svnUploadDirectory": py.get("svn_upload_directory", "前端"),
        "svnLocations": py.get("svn_locations") or py.get("svnLocations") or [],
        "buildCommand": py.get("build_command", "deploy.sh"),
        "buildCommands": py.get("build_commands") or {},
        "artifactPaths": py.get("artifact_paths") or ["dist"],
        "projectArtifactPaths": py.get("project_artifact_paths") or {},
        "orderDirPath": py.get("order_dir_path", ""),
        "selectedProjects": py.get("selected_projects") or py.get("selectedProjects") or [],
        "projectBranches": py.get("project_branches") or py.get("projectBranches") or {},
        "projectSvnLeaves": py.get("project_svn_leaves") or py.get("projectSvnLeaves") or {},
        "projectSvnRoots": py.get("project_svn_roots") or py.get("projectSvnRoots") or {},
        "projectServerPaths": py.get("project_server_paths") or py.get("projectServerPaths") or py.get("server_upload_paths") or {},
        "projectBuildCommands": py.get("project_build_commands") or py.get("projectBuildCommands") or py.get("build_commands") or {},
        "branchBuildCommands": py.get("branch_build_commands") or py.get("branchBuildCommands") or {},
        "tools": {
            "git": tools.get("git", ""),
            "bash": tools.get("bash", ""),
            "svn": tools.get("svn", ""),
            "node": tools.get("node", ""),
            "npm": tools.get("npm", ""),
        },
        "uploadAfterBuild": False if py.get("mode") == "local" else (py.get("auto_install_deps") is not False),
        "uploadToServer": py.get("mode") == "server",
        "localOutputDir": py.get("local_output", ""),
        "serverUploadPaths": py.get("server_upload_paths") or {},
        "enableDeskPet": py.get("enable_desk_pet") is not False,
        "deskPetStyle": "blob" if py.get("desk_pet_style") == "blob" else "pixel",
        "form": {
            "hospitalName": py.get("hospital_name", ""),
            "orderNo": py.get("order_no", ""),
            "orderNotes": py.get("order_notes", ""),
            "createOrderDir": py.get("create_order_dir", False),
            "svnUsername": svn_creds.get("username", ""),
            "svnPassword": svn_creds.get("password", ""),
            "serverAddress": server.get("host", ""),
            "serverUsername": server.get("username", ""),
            "serverPassword": server.get("password", ""),
        },
    }


def frontend_config_to_py(fe: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(fe, dict):
        fe = {}
    form = fe.get("form") or {}
    artifact_paths = fe.get("artifactPaths") or ["dist"]
    if isinstance(artifact_paths, str):
        artifact_paths = [s.strip() for s in artifact_paths.replace(";", ",").split(",") if s.strip()]

    tools = fe.get("tools") or {}
    return {
        "mode": "server" if fe.get("uploadToServer") else ("local" if fe.get("uploadAfterBuild") is False else "svn"),
        "root_path": fe.get("rootPath", ""),
        "svn_root": fe.get("svnRootUrl", ""),
        "svn_upload_directory": fe.get("svnUploadDirectory", "前端"),
        "svn_locations": fe.get("svnLocations") or [],
        "local_output": fe.get("localOutputDir", ""),
        "order_dir_path": fe.get("orderDirPath", ""),
        "create_order_dir": bool(form.get("createOrderDir")),
        "build_command": (fe.get("buildCommand") or "deploy.sh").strip(),
        "build_commands": fe.get("buildCommands") or {},
        "artifact_paths": artifact_paths if artifact_paths else ["dist"],
        "project_artifact_paths": fe.get("projectArtifactPaths") or {},
        "selected_projects": fe.get("selectedProjects") or [],
        "project_branches": fe.get("projectBranches") or {},
        "project_svn_leaves": fe.get("projectSvnLeaves") or {},
        "project_svn_roots": fe.get("projectSvnRoots") or {},
        "project_server_paths": fe.get("projectServerPaths") or fe.get("serverUploadPaths") or {},
        "project_build_commands": fe.get("projectBuildCommands") or fe.get("buildCommands") or {},
        "branch_build_commands": fe.get("branchBuildCommands") or {},
        "auto_install_deps": True,
        "auto_pull": True,
        "skip_svn_commit": False,
        "node_required_version": "14.21.3",
        "tools": {
            "git": tools.get("git", ""),
            "bash": tools.get("bash", ""),
            "svn": tools.get("svn", ""),
            "node": tools.get("node", ""),
            "npm": tools.get("npm", ""),
        },
        "svn_credentials": {
            "username": form.get("svnUsername", ""),
            "password": form.get("svnPassword", ""),
        },
        "server": {
            "host": form.get("serverAddress", ""),
            "username": form.get("serverUsername", ""),
            "password": form.get("serverPassword", ""),
        },
        "hospital_name": form.get("hospitalName", ""),
        "order_no": form.get("orderNo", ""),
        "order_notes": form.get("orderNotes", ""),
        "enable_desk_pet": fe.get("enableDeskPet") is not False,
        "desk_pet_style": fe.get("deskPetStyle", "pixel"),
    }


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
def _error(code: str, message: str, status: int, details: Any = None) -> web.Response:
    body: Dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return web.json_response(body, status=status)


@web.middleware
async def security_middleware(request: web.Request, handler):
    request["profile_id"] = _profile_id(request.cookies.get(PROFILE_COOKIE))
    try:
        assert_origin_allowed(
            request.headers.get("Origin", ""), request.scheme, request.host,
            request.app.get("allowed_origins", set()),
        )
    except ValueError as exc:
        return _error("origin_rejected", str(exc), 403)
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = _error("http_error", ex.reason, ex.status)
        except KeyError:
            response = _error("not_found", "Resource not found", 404)
        except (ConfigConflict, ProfileConflict) as exc:
            response = _error("revision_conflict", str(exc), 409)
        except (ValueError, json.JSONDecodeError) as exc:
            response = _error("invalid_request", str(exc), 400)
        except Exception as exc:
            logger.exception("Unhandled exception in request %s", request.path)
            response = _error("internal_error", "Internal server error", 500)

    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self' ws: wss:"
    )
    if request.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    if request.cookies.get(PROFILE_COOKIE) != request["profile_id"]:
        response.set_cookie(
            PROFILE_COOKIE, request["profile_id"], httponly=True, samesite="Lax",
            secure=request.scheme == "https", max_age=365 * 24 * 60 * 60,
        )
    return response


# ---------------------------------------------------------------------------
# API Handlers
# ---------------------------------------------------------------------------

async def _execute_command(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    result = await runner_service.execute_command(name, payload)
    if result.get("success") is False:
        reason = " ".join(str(result.get("error") or "Command failed").splitlines())
        raise web.HTTPBadGateway(reason=reason)
    return result

async def handle_health(request: web.Request) -> web.Response:
    manager = request.app.get("task_manager")
    return web.json_response({
        "status": "ok",
        "mode": "web",
        "version": "1.0.6",
        "active_runs": len(manager._active) if manager else runner_service.running_count,
        "max_concurrency": manager.max_concurrency if manager else runner_service.max_concurrency,
    })


async def handle_config_get(request: web.Request) -> web.Response:
    value = _config_view(
        request.app["config_service"].get_public(),
        request.app["profile_store"].get_public(request["profile_id"]),
    )
    value["config"] = py_config_to_frontend(value["config"])
    return web.json_response(value)


async def handle_config_save(request: web.Request) -> web.Response:
    body = await request.json()
    if not isinstance(body, dict):
        raise ValueError("Request body must be an object")
    fe_config = body.get("config") if isinstance(body, dict) and "config" in body else body
    revision = body.get("revision", "") if isinstance(body, dict) else ""
    clear_secrets = body.get("clearSecrets", []) if isinstance(body, dict) else []
    clear_secrets = [
        {"form.svnPassword": "svn_credentials.password",
         "form.serverPassword": "server.password"}.get(item, item)
        for item in clear_secrets
    ]
    try:
        result = request.app["profile_store"].save(
            request["profile_id"], _personal_config(frontend_config_to_py(fe_config)),
            revision,
        )
    except Exception:
        request.app["task_store"].record_audit(
            "config.save", "failed", submitter=str(body.get("submitter") or ""),
            remote_ip=request.remote or "",
        )
        raise
    request.app["task_store"].record_audit(
        "config.save", "success", submitter=str(body.get("submitter") or ""),
        remote_ip=request.remote or "",
    )
    result = _config_view(request.app["config_service"].get_public(), result)
    result["config"] = py_config_to_frontend(result["config"])
    return web.json_response(result)


async def handle_tools_detect(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("detect-tools", payload)
    return web.json_response({
        "tools": res.get("tools", {}),
        "status": res.get("status", {}),
    })


async def handle_tools_launch(request: web.Request) -> web.Response:
    payload = await request.json()
    return web.json_response({"success": True, "mode": "web_notice", "message": "Web模式下不支持直接调起客户端本地程序"})


async def handle_projects_discover(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("discover", payload)
    raw_projects = res.get("projects", [])
    formatted = [
        {
            "projectName": p.get("name", ""),
            "repoPath": p.get("path", ""),
            "currentBranch": p.get("current_branch", ""),
            "branches": p.get("branches") or [],
            "defaultSvnLeaf": p.get("default_svn_leaf", ""),
            "serverUploadPath": p.get("server_upload_path", ""),
            "buildCommand": p.get("build_command", ""),
        }
        for p in raw_projects
    ]
    return web.json_response(formatted)


async def handle_projects_refresh_branches(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("refresh-branches", payload)
    return web.json_response({
        "projectName": res.get("project_name") or payload.get("projectName") or "",
        "repoPath": payload.get("repoPath", ""),
        "currentBranch": res.get("current_branch", ""),
        "branches": res.get("branches") or [],
    })


async def handle_projects_check_local_changes(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("check-local-changes", payload)
    changes = res.get("changes", [])
    formatted = [
        {
            "dirty": c.get("has_changes", False),
            "total": (c.get("staged_count") or 0) + (c.get("unstaged_count") or 0) + (c.get("untracked_count") or 0),
            "files": (c.get("staged") or []) + (c.get("unstaged") or []) + (c.get("untracked") or []),
            "truncated": False,
            "project": c.get("project", ""),
            "repoPath": "",
            "branch": c.get("branch", ""),
        }
        for c in changes
    ]
    return web.json_response(formatted)


async def handle_affected_detect(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("detect-affected", payload)
    return web.json_response({
        "affectedProjects": res.get("affected_projects", []),
        "baseRef": res.get("base_ref", "main"),
        "headRef": res.get("head_ref", "HEAD"),
    })


async def handle_affected_detect_staged(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("detect-affected-staged", payload)
    return web.json_response({
        "affectedProjects": res.get("affected_projects", []),
    })


async def handle_svn_list(request: web.Request) -> web.Response:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise ValueError("Request body must be an object")

    # The web client deliberately receives a masked password.  Substitute the
    # server-side secret before invoking SVN, while preserving newly entered
    # credentials from the client.
    execution_config = request.app["execution_config"](request)
    _assert_allowed_svn_url(payload.get("url"), execution_config)
    payload["svn"] = (execution_config.get("tools") or {}).get("svn", payload.get("svn", ""))
    stored_credentials = execution_config.get(
        "svn_credentials", {}
    )
    for field, stored_field in (("username", "username"), ("password", "password")):
        if payload.get(field) in (None, "", "[configured]"):
            payload[field] = stored_credentials.get(stored_field, "")

    res = await _execute_command("svn-list", payload)
    raw_entries = res.get("items") or res.get("entries") or []
    if isinstance(raw_entries, list):
        entries = []
        for e in raw_entries:
            if isinstance(e, dict):
                name = (e.get("name") or "").rstrip("/")
            else:
                name = str(e).rstrip("/")
            if name:
                entries.append(name)
    else:
        entries = []
    return web.json_response(entries)


async def handle_server_test(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("server-test", payload)
    return web.json_response(res)


async def handle_order_deploy_list(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("order-deploy-list", payload)
    return web.json_response(res)


async def handle_order_deploy_open_file(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("order-deploy-open-file", payload)
    return web.json_response(res)


async def handle_order_dir_create(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("create-order-dir", payload)
    return web.json_response(res)


async def handle_templates_list(request: web.Request) -> web.Response:
    res = await _execute_command("template-list", {})
    return web.json_response(res.get("templates", res.get("data", res)))


async def handle_template_get(request: web.Request) -> web.Response:
    t_id = request.match_info["id"]
    res = await _execute_command("template-get", {"id": t_id})
    return web.json_response(res.get("template", res.get("data", res)))


async def handle_template_save(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await _execute_command("template-save", payload)
    return web.json_response(res.get("template", res.get("data", res)))


async def handle_template_delete(request: web.Request) -> web.Response:
    t_id = request.match_info["id"]
    res = await _execute_command("template-delete", {"id": t_id})
    return web.json_response(res)


async def handle_history_list(request: web.Request) -> web.Response:
    res = await _execute_command("history-list", {})
    return web.json_response(res.get("records", res.get("data", res)))


async def handle_history_get(request: web.Request) -> web.Response:
    h_id = request.match_info["id"]
    res = await _execute_command("history-get", {"id": h_id})
    return web.json_response(res.get("record", res.get("data", res)))


async def handle_mock_query_request(request: web.Request) -> web.Response:
    payload = await request.json()
    target_url = payload.get("url", "")
    method = payload.get("method", "GET").upper()
    body = payload.get("body")

    try:
        target = resolve_safe_proxy_target(
            target_url, method, request.app.get("proxy_allowed_hosts", set())
        )
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "zbuild-MockQueryTool/2.0",
        }
        connector = aiohttp.TCPConnector(resolver=PinnedResolver(target))
        async with aiohttp.ClientSession(connector=connector) as session:
            kwargs: Dict[str, Any] = {
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=10),
                "allow_redirects": False,
            }
            if body is not None and method != "GET":
                if isinstance(body, (dict, list)):
                    kwargs["json"] = body
                else:
                    kwargs["data"] = str(body).encode("utf-8")
                    headers["Content-Type"] = "application/json"

            async with session.request(method, target_url, **kwargs) as resp:
                text_data = await resp.text()
                try:
                    data = json.loads(text_data)
                    return web.json_response(data, status=resp.status)
                except Exception:
                    return web.Response(
                        text=text_data,
                        status=resp.status,
                        content_type=resp.content_type or "text/plain",
                    )
    except Exception as e:
        return _error("proxy_failed", f"代理请求目标服务器失败: {e}", 502)


async def handle_db_test_connection(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await asyncio.to_thread(test_db_connection, payload)
    request.app["task_store"].record_audit(
        "database.test", "success" if res.get("success") else "failed",
        submitter=str(payload.get("submitter") or ""), remote_ip=request.remote or "",
    )
    if res.get("success") is False:
        raise web.HTTPBadGateway(reason=str(res.get("error") or "Database test failed"))
    return web.json_response(res)


async def handle_db_execute_sql(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await asyncio.to_thread(execute_db_sql, payload)
    request.app["task_store"].record_audit(
        "database.execute", "success" if res.get("success") else "failed",
        submitter=str(payload.get("submitter") or ""), remote_ip=request.remote or "",
    )
    if res.get("success") is False:
        raise web.HTTPBadGateway(reason=str(res.get("error") or "Database command failed"))
    return web.json_response(res)


















# ---------------------------------------------------------------------------
# SPA Static File Fallback Handler
# ---------------------------------------------------------------------------

async def handle_static_spa(request: web.Request) -> web.StreamResponse:
    dist_dir = PROJECT_ROOT / "dist"
    req_path = request.path.lstrip("/")

    if not req_path:
        target_file = dist_dir / "index.html"
    else:
        target_file = dist_dir / req_path

    # Security check: prevent directory traversal
    try:
        resolved = target_file.resolve()
        resolved.relative_to(dist_dir.resolve())
    except (OSError, ValueError):
        raise web.HTTPForbidden(reason="Invalid static asset path")

    if not resolved.exists() or resolved.is_dir():
        resolved = dist_dir / "index.html"

    if not resolved.exists():
        return web.Response(
            text="<h1>zbuild Web Server</h1><p>Frontend assets not found in dist/. Please run <code>npm run build</code> first.</p>",
            content_type="text/html",
            status=200
        )

    mime_type, _ = mimetypes.guess_type(str(resolved))
    if mime_type is None:
        mime_type = "application/octet-stream"

    return web.FileResponse(resolved)


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(
    *, data_dir: Optional[Path] = None, task_store=None, task_manager=None,
    workspace=None, config_service=None, runner=None,
) -> web.Application:
    data_root = Path(
        data_dir or os.environ.get("ZBUILD_DATA_DIR") or (PROJECT_ROOT / ".zbuild-data")
    ).resolve()
    data_root.mkdir(parents=True, exist_ok=True)
    owned_store = task_store is None
    store = task_store or TaskStore(data_root)
    owned_profiles = True
    profile_store = ProfileStore(data_root) if owned_profiles else None
    workspace_service = workspace or WorkspaceManager(data_root, {})
    manager = task_manager or TaskManager(
        store, runner or runner_service, workspace_service,
        max_concurrency=int(os.environ.get("ZBUILD_MAX_CONCURRENCY", "2")),
    )
    config = config_service or WebConfigService(data_root / "web-config.json")
    if config_service is None and not config.path.exists():
        from core.config import load_config
        config.save(load_config(), "0")
    app = web.Application(middlewares=[security_middleware], client_max_size=1024 * 1024)
    app["task_store"] = store
    app["task_manager"] = manager
    app["workspace"] = workspace_service
    app["config_service"] = config
    app["profile_store"] = profile_store
    app["execution_config"] = lambda request: _execution_config(
        config.get_execution_config(), profile_store.get_execution_config(request["profile_id"])
    )
    app["allowed_origins"] = {
        value.strip() for value in os.environ.get("ZBUILD_ALLOWED_ORIGINS", "").split(",")
        if value.strip()
    }
    app["proxy_allowed_hosts"] = {
        value.strip().lower() for value in os.environ.get("ZBUILD_PROXY_ALLOWLIST", "").split(",")
        if value.strip()
    }

    async def lifecycle(application: web.Application):
        await application["task_manager"].start()
        yield
        await application["task_manager"].shutdown()
        if owned_store:
            application["task_store"].close()
        if owned_profiles:
            application["profile_store"].close()

    app.cleanup_ctx.append(lifecycle)

    # REST APIs
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/config", handle_config_get)
    app.router.add_put("/api/config", handle_config_save)
    app.router.add_post("/api/tools/detect", handle_tools_detect)
    app.router.add_post("/api/tools/launch", handle_tools_launch)
    app.router.add_post("/api/projects/discover", handle_projects_discover)
    app.router.add_post("/api/projects/refresh-branches", handle_projects_refresh_branches)
    app.router.add_post("/api/projects/check-local-changes", handle_projects_check_local_changes)
    app.router.add_post("/api/affected/detect", handle_affected_detect)
    app.router.add_post("/api/affected/detect-staged", handle_affected_detect_staged)
    app.router.add_post("/api/svn/list", handle_svn_list)
    app.router.add_post("/api/server/test", handle_server_test)
    app.router.add_post("/api/order-deploy/list", handle_order_deploy_list)
    app.router.add_post("/api/order-deploy/open-file", handle_order_deploy_open_file)
    app.router.add_post("/api/order-dir/create", handle_order_dir_create)
    app.router.add_get("/api/templates", handle_templates_list)
    app.router.add_get("/api/templates/{id}", handle_template_get)
    app.router.add_post("/api/templates", handle_template_save)
    app.router.add_delete("/api/templates/{id}", handle_template_delete)
    app.router.add_get("/api/history", handle_history_list)
    app.router.add_get("/api/history/{id}", handle_history_get)
    app.router.add_post("/api/mock-query/request", handle_mock_query_request)
    app.router.add_post("/api/db/test-connection", handle_db_test_connection)
    app.router.add_post("/api/db/execute-sql", handle_db_execute_sql)

    register_task_routes(app)

    # Static assets and SPA fallback
    app.router.add_get("/{tail:.*}", handle_static_spa)

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 60)
    print(f"  zbuild Web Server running on http://{host}:{port}")
    print(f"  Local Access: http://127.0.0.1:{port}")
    print("=" * 60)
    web.run_app(create_app(), host=host, port=port)

# -*- coding: utf-8 -*-
"""aiohttp Web and WebSocket Application for zbuild."""

import asyncio
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
from aiohttp import web

# Ensure the scripts directory is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.runner_service import runner_service
from server.db_service import test_db_connection, execute_db_sql


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("zbuild-server")


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
@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as exc:
            logger.error("Unhandled exception in request %s: %s", request.path, exc)
            response = web.json_response({"success": False, "error": str(exc)}, status=500)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response


# ---------------------------------------------------------------------------
# API Handlers
# ---------------------------------------------------------------------------

async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "mode": "web",
        "version": "1.0.6",
        "active_runs": runner_service.running_count,
        "max_concurrency": runner_service.max_concurrency,
    })


async def handle_config_get(request: web.Request) -> web.Response:
    res = await runner_service.execute_command("config", {})
    raw_config = res.get("config", res.get("data", res))
    return web.json_response(py_config_to_frontend(raw_config))


async def handle_config_save(request: web.Request) -> web.Response:
    fe_config = await request.json()
    py_config = frontend_config_to_py(fe_config)
    await runner_service.execute_command("save-config", {"config": py_config})
    return web.json_response(fe_config)


async def handle_tools_detect(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("detect-tools", payload)
    return web.json_response({
        "tools": res.get("tools", {}),
        "status": res.get("status", {}),
    })


async def handle_tools_launch(request: web.Request) -> web.Response:
    payload = await request.json()
    return web.json_response({"success": True, "mode": "web_notice", "message": "Web模式下不支持直接调起客户端本地程序"})


async def handle_projects_discover(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("discover", payload)
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
    res = await runner_service.execute_command("refresh-branches", payload)
    return web.json_response({
        "projectName": res.get("project_name") or payload.get("projectName") or "",
        "repoPath": payload.get("repoPath", ""),
        "currentBranch": res.get("current_branch", ""),
        "branches": res.get("branches") or [],
    })


async def handle_projects_check_local_changes(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("check-local-changes", payload)
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
    res = await runner_service.execute_command("detect-affected", payload)
    return web.json_response({
        "affectedProjects": res.get("affected_projects", []),
        "baseRef": res.get("base_ref", "main"),
        "headRef": res.get("head_ref", "HEAD"),
    })


async def handle_affected_detect_staged(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("detect-affected-staged", payload)
    return web.json_response({
        "affectedProjects": res.get("affected_projects", []),
    })


async def handle_svn_list(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("svn-list", payload)
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
    res = await runner_service.execute_command("server-test", payload)
    return web.json_response(res)


async def handle_order_deploy_list(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("order-deploy-list", payload)
    return web.json_response(res)


async def handle_order_deploy_open_file(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("order-deploy-open-file", payload)
    return web.json_response(res)


async def handle_order_dir_create(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("create-order-dir", payload)
    return web.json_response(res)


async def handle_templates_list(request: web.Request) -> web.Response:
    res = await runner_service.execute_command("template-list", {})
    return web.json_response(res.get("templates", res.get("data", res)))


async def handle_template_get(request: web.Request) -> web.Response:
    t_id = request.match_info["id"]
    res = await runner_service.execute_command("template-get", {"id": t_id})
    return web.json_response(res.get("template", res.get("data", res)))


async def handle_template_save(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await runner_service.execute_command("template-save", payload)
    return web.json_response(res.get("template", res.get("data", res)))


async def handle_template_delete(request: web.Request) -> web.Response:
    t_id = request.match_info["id"]
    res = await runner_service.execute_command("template-delete", {"id": t_id})
    return web.json_response(res)


async def handle_history_list(request: web.Request) -> web.Response:
    res = await runner_service.execute_command("history-list", {})
    return web.json_response(res.get("records", res.get("data", res)))


async def handle_history_get(request: web.Request) -> web.Response:
    h_id = request.match_info["id"]
    res = await runner_service.execute_command("history-get", {"id": h_id})
    return web.json_response(res.get("record", res.get("data", res)))


async def handle_mock_query_request(request: web.Request) -> web.Response:
    payload = await request.json()
    target_url = payload.get("url", "")
    method = payload.get("method", "GET").upper()
    body = payload.get("body")

    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "zbuild-MockQueryTool/2.0",
        }
        async with aiohttp.ClientSession() as session:
            kwargs: Dict[str, Any] = {
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=10),
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
        return web.json_response({"success": False, "error": f"代理请求目标服务器失败: {e}"}, status=502)


async def handle_db_test_connection(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await asyncio.to_thread(test_db_connection, payload)
    return web.json_response(res)


async def handle_db_execute_sql(request: web.Request) -> web.Response:
    payload = await request.json()
    res = await asyncio.to_thread(execute_db_sql, payload)
    return web.json_response(res)


# ---------------------------------------------------------------------------
# WebSocket Runner Handler
# ---------------------------------------------------------------------------

async def handle_ws_run(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=15.0)
    await ws.prepare(request)
    logger.info("WebSocket client connected from %s", request.remote)

    current_task_id = f"task_{id(ws)}"

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                action = data.get("action")

                if action == "start":
                    command_name = data.get("command", "run")
                    payload = data.get("payload", {})
                    task_id = data.get("taskId") or current_task_id

                    async def on_event(event_data: Dict[str, Any]):
                        if not ws.closed:
                            await ws.send_str(json.dumps({"type": "event", "payload": event_data}, ensure_ascii=False))

                    async def on_exit(code: int):
                        if not ws.closed:
                            await ws.send_str(json.dumps({"type": "exit", "payload": {"code": code}}, ensure_ascii=False))

                    asyncio.create_task(
                        runner_service.stream_run(
                            command_name=command_name,
                            payload=payload,
                            event_callback=on_event,
                            exit_callback=on_exit,
                            task_id=task_id,
                        )
                    )

                elif action == "stop":
                    task_id = data.get("taskId") or current_task_id
                    success = await runner_service.stop_run(task_id)
                    await ws.send_str(json.dumps({"type": "stopped", "success": success}))

                elif action == "ping":
                    await ws.send_str(json.dumps({"type": "pong"}))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.warning("WebSocket error: %s", ws.exception())
    finally:
        await runner_service.stop_run(current_task_id)
        logger.info("WebSocket client disconnected")

    return ws


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
        if not str(resolved).startswith(str(dist_dir.resolve())):
            return web.HTTPForbidden()
    except Exception:
        resolved = dist_dir / "index.html"

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

def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware])

    # REST APIs
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/config", handle_config_get)
    app.router.add_post("/api/config", handle_config_save)
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

    # WebSocket
    app.router.add_get("/api/ws/run", handle_ws_run)

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

# -*- coding: utf-8 -*-
"""REST and WebSocket routes for persistent team tasks."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
from aiohttp import web

from server.workspace import assert_within


def _trusted_projects(config: Dict[str, Any], requested: List[Dict[str, Any]]) -> Dict[str, Path]:
    root_value = config.get("root_path")
    if not root_value:
        return {}
    root = Path(root_value).resolve()
    projects: Dict[str, Path] = {}
    for item in requested:
        name = str(item.get("name") or "") if isinstance(item, dict) else ""
        if not name:
            continue
        candidate = (root / name).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if (candidate / ".git").exists():
            projects[name] = candidate
    return projects


async def create_task(request: web.Request) -> web.Response:
    body = await request.json()
    if not isinstance(body, dict):
        raise ValueError("Request body must be an object")
    payload = body.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    task_type = str(body.get("type") or "")
    execution_config = request.app["execution_config"](request)
    if task_type == "run":
        requested_projects = payload.get("projects") or []
        if not isinstance(requested_projects, list) or not requested_projects:
            raise ValueError("At least one project is required")
        trusted = _trusted_projects(execution_config, requested_projects)
        requested_names = {
            str(item.get("name") or "") for item in requested_projects
            if isinstance(item, dict)
        }
        if not requested_names or requested_names != set(trusted):
            raise ValueError("One or more projects are not configured server repositories")
        # The browser may choose projects, branches, and order metadata, but
        # never filesystem roots, executable paths, or SVN/server endpoints.
        safe_projects = [
            {"name": str(item.get("name") or ""), "branch": str(item.get("branch") or "")}
            for item in requested_projects if isinstance(item, dict)
        ]
        safe_request = {
            key: payload[key] for key in (
                "hospitalName", "orderNo", "orderNotes", "mode",
                "createOrderDir", "uploadAfterBuild", "uploadToServer",
            ) if key in payload
        }
        safe_request["projects"] = safe_projects
        payload = dict(execution_config)
        payload.update(safe_request)
        payload["_trusted_projects"] = {name: str(path) for name, path in trusted.items()}
    elif task_type == "order-deploy-run":
        payload = dict(payload)
        svn = execution_config.get("svn_credentials") or {}
        server = execution_config.get("server") or {}
        defaults = {
            "svnUsername": svn.get("username", ""),
            "svnPassword": svn.get("password", ""),
            "serverAddress": server.get("host", ""),
            "serverUsername": server.get("username", ""),
            "serverPassword": server.get("password", ""),
        }
        for key, value in defaults.items():
            if payload.get(key) in (None, "", "[configured]"):
                payload[key] = value
    task = await request.app["task_manager"].submit_task(
        str(body.get("requestId") or ""), task_type,
        str(body.get("submitter") or ""), payload, request.remote or "",
        request["profile_id"],
    )
    return web.json_response(task, status=202)


async def list_tasks(request: web.Request) -> web.Response:
    tasks = request.app["task_store"].list_tasks(
        request.query.get("status"), request.query.get("submitter"),
        request.query.get("createdAfter"), request.query.get("createdBefore"),
        int(request.query.get("limit", "100")), int(request.query.get("offset", "0")),
        profile_id=request["profile_id"],
    )
    return web.json_response(tasks)


async def get_task(request: web.Request) -> web.Response:
    task = request.app["task_store"].get_task(
        request.match_info["task_id"], profile_id=request["profile_id"]
    )
    if not task:
        raise KeyError(request.match_info["task_id"])
    return web.json_response(task)


async def cancel_task(request: web.Request) -> web.Response:
    body = await request.json() if request.can_read_body else {}
    task = await request.app["task_manager"].cancel_task(
        request.match_info["task_id"], str(body.get("submitter") or ""),
        request.remote or "", request["profile_id"],
    )
    return web.json_response(task)


async def list_events(request: web.Request) -> web.Response:
    task_id = request.match_info["task_id"]
    if not request.app["task_store"].get_task(
        task_id, detail=False, profile_id=request["profile_id"]
    ):
        raise KeyError(task_id)
    after = int(request.query.get("after", "0"))
    if after < 0:
        raise ValueError("after must not be negative")
    return web.json_response(request.app["task_store"].list_events(task_id, after))


async def download_artifact(request: web.Request) -> web.StreamResponse:
    task_id = request.match_info["task_id"]
    if not request.app["task_store"].get_task(
        task_id, detail=False, profile_id=request["profile_id"]
    ):
        raise KeyError(task_id)
    path = request.app["task_store"].get_artifact_path(
        task_id, request.match_info["artifact_id"]
    )
    if not path or not path.is_file():
        raise KeyError(request.match_info["artifact_id"])
    assert_within(path, request.app["workspace"].artifact_root)
    return web.FileResponse(path)


async def task_websocket(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=15.0)
    await ws.prepare(request)
    manager = request.app["task_manager"]
    subscription = None
    task_id = ""
    try:
        message = await ws.receive(timeout=15)
        if message.type != aiohttp.WSMsgType.TEXT:
            await ws.close(code=1008, message=b"subscription required")
            return ws
        data = json.loads(message.data)
        if data.get("action") != "subscribe":
            await ws.close(code=1008, message=b"invalid action")
            return ws
        task_id = str(data.get("taskId") or "")
        after = int(data.get("after") or 0)
        if not request.app["task_store"].get_task(
            task_id, detail=False, profile_id=request["profile_id"]
        ):
            await ws.close(code=1008, message=b"task not found")
            return ws
        subscription = manager.subscribe(task_id)
        for event in request.app["task_store"].list_events(task_id, after):
            await ws.send_json({"type": "task_event", "payload": event})
        while not ws.closed:
            receive_task = asyncio.create_task(ws.receive())
            event_task = asyncio.create_task(subscription.get())
            done, pending = await asyncio.wait(
                {receive_task, event_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for pending_task in pending:
                pending_task.cancel()
            if receive_task in done:
                incoming = receive_task.result()
                if incoming.type in {
                    aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.ERROR,
                }:
                    break
                if incoming.type != aiohttp.WSMsgType.TEXT:
                    await ws.close(code=1008, message=b"invalid action")
                    break
                value = json.loads(incoming.data)
                if value.get("action") != "ping":
                    await ws.close(code=1008, message=b"invalid action")
                    break
                await ws.send_json({"type": "pong"})
            else:
                await ws.send_json({"type": "task_event", "payload": event_task.result()})
    except (asyncio.TimeoutError, ConnectionResetError):
        pass
    finally:
        if subscription is not None:
            manager.unsubscribe(task_id, subscription)
    return ws


def register_task_routes(app: web.Application) -> None:
    app.router.add_post("/api/tasks", create_task)
    app.router.add_get("/api/tasks", list_tasks)
    app.router.add_get("/api/tasks/{task_id}", get_task)
    app.router.add_post("/api/tasks/{task_id}/cancel", cancel_task)
    app.router.add_get("/api/tasks/{task_id}/events", list_events)
    app.router.add_get("/api/tasks/{task_id}/artifacts/{artifact_id}", download_artifact)
    app.router.add_get("/api/ws/tasks", task_websocket)

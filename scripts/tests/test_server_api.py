# -*- coding: utf-8 -*-
"""Unit tests for the zbuild Web server API and WebSocket runner."""

import asyncio
import json
import unittest
from pathlib import Path
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

import sys
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.app import create_app


class TestWebServerAPI(AioHTTPTestCase):
    async def get_application(self):
        return create_app()

    @unittest_run_loop
    async def test_health_check(self):
        resp = await self.client.request("GET", "/api/health")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "web")

    @unittest_run_loop
    async def test_templates_and_history_api(self):
        resp = await self.client.request("GET", "/api/templates")
        self.assertEqual(resp.status, 200)
        data = await resp.json()
        self.assertIsInstance(data, list)

        resp2 = await self.client.request("GET", "/api/history")
        self.assertEqual(resp2.status, 200)
        data2 = await resp2.json()
        self.assertIsInstance(data2, list)

    @unittest_run_loop
    async def test_ws_connection_and_ping(self):
        ws = await self.client.ws_connect("/api/ws/run")
        await ws.send_str(json.dumps({"action": "ping"}))
        msg = await ws.receive_str()
        data = json.loads(msg)
        self.assertEqual(data.get("type"), "pong")
        await ws.close()


if __name__ == "__main__":
    unittest.main()

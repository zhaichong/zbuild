# -*- coding: utf-8 -*-
"""Launcher for the zbuild Web server."""

import argparse
import logging
import os
import socket
import sys
import webbrowser
from pathlib import Path

# Fix Windows console encoding issues for Unicode/Emoji
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from aiohttp import web
from server.app import create_app


def get_local_ip() -> str:
    """Get the primary local LAN IP address for colleagues to connect to."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port: int = 8000) -> int:
    """Find an available port starting from start_port."""
    for p in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return start_port


def main():
    parser = argparse.ArgumentParser(description="zbuild Web Service Launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on (default: auto)")
    parser.add_argument("--open", action="store_true", help="Automatically open browser on start")
    args = parser.parse_args()

    port = args.port or find_available_port(8000)
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{port}"
    lan_url = f"http://{local_ip}:{port}"

    print("=" * 60)
    print("  [*] 智慧病房系统构建与调试工具 Web 服务已启动 (web1.0)")
    print(f"  [*] 本机访问地址:    {local_url}")
    print(f"  [*] 局域网同事访问:  {lan_url}")
    print(f"  [*] 服务模式:        集中式轻量构建 (免安装 / 零本地开销)")
    print("=" * 60)

    if args.open:
        try:
            webbrowser.open(local_url)
        except Exception:
            pass

    app = create_app()
    web.run_app(app, host=args.host, port=port, print=None)


if __name__ == "__main__":
    main()

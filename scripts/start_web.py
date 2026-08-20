# -*- coding: utf-8 -*-
"""Launcher for the zbuild Web server."""

import argparse
import logging
import os
import socket
import shutil
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
os.environ.setdefault("ZBUILD_DATA_DIR", str(PROJECT_ROOT / ".zbuild-data"))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from aiohttp import web
    from server.app import create_app
    from tools.bundled import bundled_git, bundled_node, bundled_svn
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"缺少 Python 运行依赖 {exc.name!r}；请先执行: py -m pip install -e ."
    ) from exc


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


def resolve_runtime_tools() -> list[str]:
    """Prefer packaged Git/SVN/Node so the Web bundle needs no system tools."""
    missing: list[str] = []
    for name, resolver in (("git", bundled_git), ("node", bundled_node), ("svn", bundled_svn)):
        executable = resolver()
        if executable:
            executable_dir = str(Path(executable).parent)
            path_parts = os.environ.get("PATH", "").split(os.pathsep)
            if executable_dir not in path_parts:
                os.environ["PATH"] = executable_dir + os.pathsep + os.environ.get("PATH", "")
        elif not shutil.which(name):
            missing.append(name)
    return missing


def main():
    parser = argparse.ArgumentParser(description="zbuild Web Service Launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on (default: auto)")
    parser.add_argument("--open", action="store_true", help="Automatically open browser on start")
    args = parser.parse_args()

    missing = resolve_runtime_tools()
    required_missing = [name for name in missing if name in {"git", "node"}]
    if required_missing:
        parser.error("缺少必需运行时: " + ", ".join(required_missing))
    if "svn" in missing:
        print("[WARN] 未检测到 SVN；本地构建可用，但 SVN 上传任务会失败。")

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

    try:
        app = create_app()
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"[ERROR] Web 服务安全配置初始化失败: {exc}") from exc
    web.run_app(app, host=args.host, port=port, print=None)


if __name__ == "__main__":
    main()

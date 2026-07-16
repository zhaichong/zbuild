# -*- coding: utf-8 -*-
"""Module-level constants, dataclasses, and workflow definitions."""
from dataclasses import dataclass, field
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = APP_DIR / "references" / "tool-config.json"
PROJECT_DEFAULTS_PATH = APP_DIR / "references" / "project-defaults.json"
BUILD_HISTORY_PATH = APP_DIR / "references" / "build-history.json"
DEBUG_LOG_PATH = APP_DIR / "tmp" / "python-tool-debug.log"
HISTORY_DIR = APP_DIR / "references" / "history"
TEMPLATES_DIR = APP_DIR / "references" / "templates"
APP_ICON_PATH = APP_DIR / "assets" / "app.ico"
UPGRADE_DOC_NAME = "全部升级说明.docx"
UPGRADE_DOC_PATH = APP_DIR / UPGRADE_DOC_NAME
DEFAULT_SVN_ROOT = "https://10.1.1.120/svn/智慧病房特殊订单"

WORKFLOW_STEPS = [
    "检查 Git/Bash/SVN 工具",
    "切换 Git 分支",
    "拉取当前分支最新代码",
    "检查并安装项目依赖",
    "执行 deploy.sh 打包",
    "选择最新 dist/*.tar.gz",
    "检查并创建 SVN 目录",
    "上传产物到 SVN",
    "SVN 提交完成",
]

WORKFLOW_STEPS_SERVER = [
    "检查 Git/Bash 工具",
    "切换 Git 分支",
    "拉取当前分支最新代码",
    "检查并安装项目依赖",
    "执行 deploy.sh 打包",
    "选择最新 dist/*.tar.gz",
    "上传产物到服务器",
]

WORKFLOW_STEPS_LOCAL = [
    "检查 Git/Bash/SVN 工具",
    "切换 Git 分支",
    "拉取当前分支最新代码",
    "检查并安装项目依赖",
    "执行 deploy.sh 打包",
    "选择最新 dist/*.tar.gz",
    "跳过 SVN，准备本地输出",
    "复制产物到本地输出目录",
    "本地打包完成",
]

DEFAULT_SERVER_UPLOAD_PATHS = {
    "zhbf-bedhead-frontend": "/home/data/web/a10",
    "zhbf-fontend": "/home/data/web/a10",
    "yarward-ntv-frontend": "/home/data/web",
    "yarward-web-frontend": "/home/data/web",
}


@dataclass
class ProjectInfo:
    """Discovered project metadata."""
    name: str
    path: Path
    current_branch: str
    branches: list[str]
    default_svn_leaf: str


@dataclass
class RunResult:
    """Result of a single project build-and-upload run."""
    project: str
    branch: str
    success: bool
    target_url: str
    artifact: str = ""
    message: str = ""

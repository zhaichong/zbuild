# -*- coding: utf-8 -*-
"""Module-level constants, dataclasses, and workflow definitions."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

APP_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR_ENV = os.environ.get("ZBUILD_DATA_DIR")
DATA_DIR = Path(_DATA_DIR_ENV).resolve() if _DATA_DIR_ENV else APP_DIR
CONFIG_PATH = (
    DATA_DIR / "tool-config.json"
    if _DATA_DIR_ENV
    else APP_DIR / "references" / "tool-config.json"
)
PROJECT_DEFAULTS_PATH = APP_DIR / "references" / "project-defaults.json"
BUILD_HISTORY_PATH = (
    DATA_DIR / "build-history.json"
    if _DATA_DIR_ENV
    else APP_DIR / "references" / "build-history.json"
)
DEBUG_LOG_PATH = (
    DATA_DIR / "logs" / "python-tool-debug.log"
    if _DATA_DIR_ENV
    else APP_DIR / "tmp" / "python-tool-debug.log"
)
HISTORY_DIR = DATA_DIR / "history" if _DATA_DIR_ENV else APP_DIR / "references" / "history"
TEMPLATES_DIR = (
    DATA_DIR / "templates" if _DATA_DIR_ENV else APP_DIR / "references" / "templates"
)
APP_ICON_PATH = APP_DIR / "assets" / "app.ico"
UPGRADE_DOC_NAME = "全部升级说明.docx"
UPGRADE_DOC_PATH = APP_DIR / UPGRADE_DOC_NAME
DEFAULT_SVN_ROOT = "https://10.1.1.120/svn/智慧病房特殊订单"
DEFAULT_BUILD_COMMAND = "deploy.sh"

DEFAULT_SERVER_UPLOAD_PATHS = {
    "yarward-ntv-frontend": "/home/data/web",
    "yarward-web-frontend": "/home/data/web",
    "zbuild": "/home/data/web",
    "zhbf-bedhead-frontend": "/home/data/web/a10",
    "zhbf-fontend": "/home/data/web/a10",
    "zhbf-frontend": "/home/data/web/a10",
    "zhbf-web": "/home/data/web",
}

DEFAULT_BUILD_COMMANDS = {
    "yarward-ntv-frontend": "deploy.sh",
    "yarward-web-frontend": "deploy.sh",
    "zbuild": "deploy.sh",
    "zhbf-bedhead-frontend": "deploy.sh",
    "zhbf-fontend": "deploy.sh",
    "zhbf-frontend": "deploy.sh",
    "zhbf-web": "deploy.sh",
}


@dataclass
class ProjectInfo:
    """Discovered project metadata."""
    name: str
    path: Path
    current_branch: str
    branches: List[str]
    default_svn_leaf: str
    svn_root: str = ""
    server_upload_path: str = ""
    build_command: str = DEFAULT_BUILD_COMMAND


@dataclass
class RunResult:
    """Result of a single project build-and-upload run."""
    project: str
    branch: str
    success: bool
    target_url: str
    artifact: str = ""
    message: str = ""

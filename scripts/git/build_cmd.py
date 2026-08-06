# -*- coding: utf-8 -*-
"""Validate and resolve project build commands.

Only allows:
  * relative scripts under the project tree (e.g. deploy.sh, ./scripts/build.sh)
  * a small set of package-manager / shell runners (npm, yarn, pnpm, npx, node, bash, sh)

Rejects path traversal, absolute paths outside the project, shell metacharacters,
and dangerous runner flags such as ``bash -c``.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import List, Tuple

from core.errors import BuildError

# First token must be one of these basenames (case-insensitive) when not a project script.
_ALLOWED_RUNNERS = frozenset({
    "npm", "npm.cmd", "npm.exe",
    "npx", "npx.cmd", "npx.exe",
    "yarn", "yarn.cmd", "yarn.exe",
    "pnpm", "pnpm.cmd", "pnpm.exe",
    "node", "node.exe",
    "bash", "bash.exe",
    "sh", "sh.exe",
})

# bash/sh flags that enable arbitrary code execution
_DANGEROUS_SHELL_FLAGS = frozenset({
    "-c", "-lc", "-ic", "--command",
})

# Characters that imply shell composition / redirection
_SHELL_META_RE = re.compile(r"[;&|`$<>\n\r]|\|\||&&")


def _basename(token: str) -> str:
    return Path(token.replace("\\", "/")).name.lower()


def _has_shell_meta(text: str) -> bool:
    return bool(_SHELL_META_RE.search(text))


def _is_absolute(token: str) -> bool:
    s = token.strip().strip('"').strip("'")
    if not s:
        return False
    if s.startswith("/") or s.startswith("\\\\"):
        return True
    # Windows drive path: C:\ or C:/
    if len(s) >= 2 and s[1] == ":" and s[0].isalpha():
        return True
    return False


def _is_under(project: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(project.resolve())
        return True
    except (ValueError, OSError):
        return False


def _normalize_rel(script: str) -> str:
    s = script.strip().replace("\\", "/")
    if s.startswith("./"):
        s = s[2:]
    return s


def validate_build_command(project_path: "Path | str", build_command: str) -> List[str]:
    """Return argv for a safe build command, or raise ``BuildError``.

    The returned list is suitable for ``subprocess`` without ``shell=True``.
    """
    project = Path(project_path).resolve()
    cmd_str = (build_command or "deploy.sh").strip()
    if not cmd_str:
        cmd_str = "deploy.sh"

    if _has_shell_meta(cmd_str):
        raise BuildError(
            f"打包命令包含不允许的 shell 元字符: {cmd_str!r}"
        )

    # Single-token project script: deploy.sh, ./scripts/x.sh
    if " " not in cmd_str.strip() and "\t" not in cmd_str:
        if _is_absolute(cmd_str):
            abs_script = Path(cmd_str)
            if not abs_script.is_file() or not _is_under(project, abs_script):
                raise BuildError(f"打包脚本必须位于项目目录内: {cmd_str}")
            rel = abs_script.resolve().relative_to(project).as_posix()
            if abs_script.suffix.lower() == ".sh" or "sh" in abs_script.name.lower():
                return ["bash", rel]
            return [str(abs_script.resolve())]

        normalized = _normalize_rel(cmd_str)
        if ".." in Path(normalized).parts:
            raise BuildError(f"打包脚本路径不允许包含 '..': {cmd_str}")

        looks_like_script = (
            cmd_str.startswith(("./", ".\\"))
            or cmd_str.lower().endswith((".sh", ".bash", ".cmd", ".bat"))
            or "/" in normalized
            or "\\" in cmd_str
            or (project / normalized).is_file()
        )
        if looks_like_script:
            script_candidate = project / normalized
            if not script_candidate.is_file():
                raise BuildError(f"打包脚本 {cmd_str} 未找到 in {project}")
            if not _is_under(project, script_candidate):
                raise BuildError(f"打包脚本路径逃逸项目目录: {cmd_str}")
            rel = script_candidate.resolve().relative_to(project).as_posix()
            name_l = script_candidate.name.lower()
            if script_candidate.suffix.lower() in {".sh", ".bash"} or name_l.endswith(".sh"):
                return ["bash", rel]
            return [str(script_candidate.resolve())]

    # Tokenized command form: npm run build, bash deploy.sh, ...
    try:
        parts = shlex.split(cmd_str, posix=False)
    except ValueError as exc:
        raise BuildError(f"无法解析打包命令: {cmd_str!r} ({exc})") from exc

    if not parts:
        raise BuildError("打包命令为空")

    for part in parts:
        if _has_shell_meta(part):
            raise BuildError(f"打包命令参数包含不允许的字符: {part!r}")

    runner = parts[0]
    runner_base = _basename(runner)

    # bash/sh deploy.sh → ensure script stays under project
    if runner_base in {"bash", "bash.exe", "sh", "sh.exe"}:
        if len(parts) < 2:
            raise BuildError("bash/sh 打包命令必须指定脚本文件")
        for p in parts[1:]:
            if not p.startswith("-"):
                continue
            base_flag = p.split("=", 1)[0]
            if base_flag in _DANGEROUS_SHELL_FLAGS or base_flag == "-c":
                raise BuildError(f"不允许的 shell 参数: {p}")
        script_arg = next((p for p in parts[1:] if not p.startswith("-")), None)
        if not script_arg:
            raise BuildError("bash/sh 打包命令必须指定脚本文件")
        script_rel = _normalize_rel(script_arg)
        if ".." in Path(script_rel).parts:
            raise BuildError(f"打包脚本路径不允许包含 '..': {script_arg}")
        if _is_absolute(script_arg):
            abs_script = Path(script_arg)
            if not _is_under(project, abs_script):
                raise BuildError(f"打包脚本必须位于项目目录内: {script_arg}")
        else:
            script_path = project / script_rel
            if script_path.exists() and not _is_under(project, script_path):
                raise BuildError(f"打包脚本路径逃逸项目目录: {script_arg}")
        return ["bash"] + parts[1:]

    if runner_base not in _ALLOWED_RUNNERS:
        allowed = ", ".join(sorted({r for r in _ALLOWED_RUNNERS if "." not in r}))
        raise BuildError(
            f"不允许的打包命令入口 {runner!r}。"
            f"仅允许项目内脚本或: {allowed}"
        )

    if _is_absolute(runner) and runner_base not in _ALLOWED_RUNNERS:
        raise BuildError(f"不允许的打包可执行文件: {runner}")

    if runner_base in {"node", "node.exe"}:
        for p in parts[1:]:
            if p in {"-e", "--eval", "-p", "--print"}:
                raise BuildError(f"不允许的 node 参数: {p}")

    return parts


def resolve_run_argv(
    project_path: "Path | str",
    build_command: str,
    *,
    bash_exe: str = "bash",
) -> Tuple[List[str], str]:
    """Validate *build_command* and substitute the configured bash executable.

    Returns ``(argv, original_cmd_str)``.
    """
    cmd_str = (build_command or "deploy.sh").strip() or "deploy.sh"
    argv = validate_build_command(project_path, cmd_str)
    if argv and _basename(argv[0]) in {"bash", "bash.exe", "sh", "sh.exe"}:
        argv = [bash_exe] + argv[1:]
    return argv, cmd_str

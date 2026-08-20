# -*- coding: utf-8 -*-
"""Prepare trusted detached Git worktrees and isolate task artifacts."""

import asyncio
import json
import mimetypes
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple


def _safe_segment(value: str) -> str:
    segment = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._")
    if not segment:
        raise ValueError("Invalid empty path segment")
    return segment[:100]


def assert_within(path: Path, root: Path) -> Path:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(Path(root).resolve())
    except ValueError as exc:
        raise ValueError("Path is outside the allowed task directory") from exc
    return resolved


class WorkspaceManager:
    def __init__(self, data_dir: Path, projects: Mapping[str, Path], git_executable: str = ""):
        self.data_dir = Path(data_dir).resolve()
        self.workspace_root = self.data_dir / "workspaces"
        self.artifact_root = self.data_dir / "artifacts"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.projects = {str(name): Path(path).resolve() for name, path in projects.items()}
        self.git = git_executable or os.environ.get("GIT_EXECUTABLE") or "git"
        self._repo_locks: Dict[Path, asyncio.Lock] = {}

    def update_projects(self, projects: Mapping[str, Path]) -> None:
        self.projects = {str(name): Path(path).resolve() for name, path in projects.items()}

    def _run_git(self, *args: str, cwd: Path = None) -> str:
        command = [self.git, *map(str, args)]
        env = dict(os.environ)
        env.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
        result = subprocess.run(
            command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "git command failed").strip()
            raise RuntimeError(message)
        return result.stdout.strip()

    async def prepare(
        self, task_id: str, payload: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
        task_segment = _safe_segment(task_id)
        prepared = json.loads(json.dumps(payload))
        task_projects = self.projects
        trusted = prepared.pop("_trusted_projects", None)
        if isinstance(trusted, dict):
            task_projects = {
                str(name): Path(path).resolve() for name, path in trusted.items()
            }
        projects = prepared.get("projects")
        if not isinstance(projects, list) or not projects:
            raise ValueError("At least one project is required")
        task_root = assert_within(self.workspace_root / task_segment, self.workspace_root)
        if task_root.exists():
            raise ValueError("Task workspace already exists")
        task_root.mkdir(parents=True)
        metadata: List[Dict[str, str]] = []
        try:
            for project in projects:
                if not isinstance(project, dict):
                    raise ValueError("Invalid project entry")
                name = str(project.get("name") or "")
                branch = str(project.get("branch") or "")
                base_repo = task_projects.get(name)
                if not base_repo:
                    raise ValueError(f"Unknown project: {name}")
                if not branch or branch.startswith("-"):
                    raise ValueError(f"Invalid branch for project {name}")
                worktree = assert_within(task_root / _safe_segment(name), task_root)
                lock = self._repo_locks.setdefault(base_repo, asyncio.Lock())
                async with lock:
                    sha = await asyncio.to_thread(
                        self._prepare_one, base_repo, branch, worktree
                    )
                project["path"] = str(worktree)
                metadata.append({
                    "name": name, "branch": branch, "sha": sha,
                    "baseRepo": str(base_repo), "worktree": str(worktree),
                })
            (task_root / "workspace.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            await self._remove_task_root(task_root, metadata)
            raise
        prepared["isolated_workspace"] = True
        prepared["auto_pull"] = False
        prepared["restore_branch"] = False
        return prepared, [
            {"name": item["name"], "branch": item["branch"], "sha": item["sha"]}
            for item in metadata
        ]

    def _prepare_one(self, base_repo: Path, branch: str, worktree: Path) -> str:
        if not (base_repo / ".git").exists():
            raise ValueError(f"Configured project is not a Git repository: {base_repo}")
        self._run_git("check-ref-format", "--branch", branch, cwd=base_repo)
        self._run_git("fetch", "--prune", "origin", branch, cwd=base_repo)
        sha = self._run_git(
            "rev-parse", f"refs/remotes/origin/{branch}^{{commit}}", cwd=base_repo
        )
        self._run_git("worktree", "add", "--detach", str(worktree), sha, cwd=base_repo)
        return sha

    async def collect_artifacts(
        self, task_id: str, result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        task_workspace = assert_within(
            self.workspace_root / _safe_segment(task_id), self.workspace_root
        )
        destination = assert_within(
            self.artifact_root / _safe_segment(task_id), self.artifact_root
        )
        collected: List[Dict[str, Any]] = []
        for project in result.get("projects") or []:
            if not isinstance(project, dict) or not isinstance(project.get("artifact"), dict):
                continue
            source_value = project["artifact"].get("path")
            if not source_value:
                continue
            source = assert_within(Path(source_value), task_workspace)
            if not source.is_file():
                continue
            destination.mkdir(parents=True, exist_ok=True)
            artifact_id = uuid.uuid4().hex
            target = destination / f"{artifact_id}-{source.name}"
            await asyncio.to_thread(shutil.copy2, source, target)
            collected.append({
                "artifactId": artifact_id,
                "name": source.name,
                "path": str(target),
                "mimeType": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
                "sizeBytes": target.stat().st_size,
            })
        return collected

    async def cleanup(self, task_id: str) -> None:
        task_root = assert_within(
            self.workspace_root / _safe_segment(task_id), self.workspace_root
        )
        if not task_root.exists():
            return
        metadata_path = task_root / "workspace.json"
        metadata = []
        if metadata_path.is_file():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = []
        await self._remove_task_root(task_root, metadata)

    async def _remove_task_root(self, task_root: Path, metadata: List[Dict[str, str]]) -> None:
        for item in reversed(metadata):
            base_repo = Path(item.get("baseRepo", ""))
            worktree = Path(item.get("worktree", ""))
            if base_repo in self.projects.values() and worktree.exists():
                try:
                    await asyncio.to_thread(
                        self._run_git, "worktree", "remove", "--force", str(worktree),
                        cwd=base_repo,
                    )
                except Exception:
                    pass
        if task_root.exists():
            await asyncio.to_thread(shutil.rmtree, task_root, True)

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


def _create_dir_link(target: Path, source: Path) -> None:
    """Create a directory junction on Windows or symlink on POSIX from target -> source."""
    target = Path(target)
    source = Path(source)
    if target.exists() or target.is_symlink():
        return
    source.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        try:
            import _winapi
            _winapi.CreateJunction(str(source), str(target))
            return
        except Exception:
            pass
        try:
            subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(target), str(source)],
                check=True,
                capture_output=True,
            )
            return
        except Exception:
            pass
    try:
        os.symlink(str(source), str(target), target_is_directory=True)
    except Exception:
        pass


def _remove_dir_link(path: Path) -> None:
    """Safely remove a symlink or junction directory without deleting target contents."""
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        return
    try:
        if path.is_symlink():
            path.unlink()
            return
    except Exception:
        pass
    if os.name == "nt":
        try:
            os.rmdir(str(path))
            return
        except Exception:
            pass


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
        self.deps_cache_root = self.data_dir / "deps_cache"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.deps_cache_root.mkdir(parents=True, exist_ok=True)
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
                # Link persistent node_modules cache for frontend/JS projects with multi-version fingerprint slot
                from git.deps import compute_deps_slot_key
                slot_key = compute_deps_slot_key(worktree)
                deps_project_root = self.deps_cache_root / _safe_segment(name)
                deps_slot_dir = deps_project_root / slot_key
                deps_cache_dir = deps_slot_dir / "node_modules"
                deps_slot_dir.mkdir(parents=True, exist_ok=True)

                # Update slot access timestamp for LRU cache pruning
                try:
                    (deps_slot_dir / ".last_accessed").write_text(str(int(asyncio.get_event_loop().time())), encoding="utf-8")
                except Exception:
                    pass

                _create_dir_link(worktree / "node_modules", deps_cache_dir)

                # Synchronize project manifest and loader configs to deps_slot_dir
                # so that loaders (postcss-loader, babel-loader) resolving realpath in
                # node_modules can correctly discover the project's configs during compilation
                for cfg_name in (
                    "package.json",
                    "package-lock.json",
                    "postcss.config.js",
                    ".postcssrc",
                    ".postcssrc.js",
                    ".postcssrc.json",
                    "babel.config.js",
                    ".babelrc",
                    ".browserslistrc",
                ):
                    src_file = worktree / cfg_name
                    if src_file.is_file():
                        try:
                            shutil.copy2(src_file, deps_slot_dir / cfg_name)
                        except Exception:
                            pass
                # Fallback postcss.config.js if none exists so postcss-load-config won't fail
                if not (deps_slot_dir / "postcss.config.js").exists() and not (deps_slot_dir / ".postcssrc").exists() and not (deps_slot_dir / ".postcssrc.js").exists():
                    try:
                        (deps_slot_dir / "postcss.config.js").write_text(
                            "module.exports = { plugins: [require('autoprefixer')()] };\n",
                            encoding="utf-8",
                        )
                    except Exception:
                        pass

                project["path"] = str(worktree)
                metadata.append({
                    "name": name, "branch": branch, "sha": sha,
                    "baseRepo": str(base_repo), "worktree": str(worktree),
                })

            # Auto-mount sibling registered projects as directory junctions/symlinks
            # so relative micro-frontend references (e.g. ../yarward-nova-ai) resolve seamlessly.
            # Scan both explicitly passed task_projects and the parent directory of base repos (e.g. D:\build).
            potential_siblings: Dict[str, Path] = dict(task_projects)
            for item in metadata:
                base_repo_dir = Path(item.get("baseRepo", "")).parent
                if base_repo_dir.is_dir():
                    try:
                        for child in base_repo_dir.iterdir():
                            if child.is_dir() and child.name not in potential_siblings and not child.name.startswith("."):
                                potential_siblings[child.name] = child
                    except Exception:
                        pass

            for sibling_name, sibling_path in potential_siblings.items():
                sibling_link = task_root / _safe_segment(sibling_name)
                if not sibling_link.exists() and sibling_path.exists():
                    try:
                        _create_dir_link(sibling_link, sibling_path)
                    except Exception:
                        pass

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
            # Safely detach node_modules junction/symlink before deleting worktree
            _remove_dir_link(worktree / "node_modules")
            if base_repo in self.projects.values() and worktree.exists():
                try:
                    await asyncio.to_thread(
                        self._run_git, "worktree", "remove", "--force", str(worktree),
                        cwd=base_repo,
                    )
                except Exception:
                    pass
        if task_root.exists():
            # Ensure any dangling directory links inside task_root are unlinked
            try:
                for sub in task_root.iterdir():
                    if sub.is_dir():
                        _remove_dir_link(sub / "node_modules")
            except Exception:
                pass
            await asyncio.to_thread(shutil.rmtree, task_root, True)

    async def prune_deps_cache(
        self, max_slots_per_project: int = 5, max_age_seconds: int = 15 * 86400
    ) -> int:
        """Prune stale dependency cache slots using an LRU policy.

        Keeps at most ``max_slots_per_project`` slots per project, removing slots
        that haven't been accessed for ``max_age_seconds``.

        Returns the number of pruned slots.
        """
        pruned_count = 0
        if not self.deps_cache_root.is_dir():
            return pruned_count

        now = int(asyncio.get_event_loop().time())

        for project_dir in self.deps_cache_root.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue

            slots: List[Tuple[Path, float]] = []
            for slot_dir in project_dir.iterdir():
                if not slot_dir.is_dir():
                    continue
                # Determine slot access time from .last_accessed or folder mtime
                access_time = 0.0
                last_accessed_file = slot_dir / ".last_accessed"
                if last_accessed_file.is_file():
                    try:
                        access_time = float(last_accessed_file.read_text(encoding="utf-8").strip())
                    except Exception:
                        access_time = slot_dir.stat().st_mtime
                else:
                    access_time = slot_dir.stat().st_mtime

                slots.append((slot_dir, access_time))

            # Sort by last accessed ascending (oldest first)
            slots.sort(key=lambda item: item[1])

            # Slots exceeding the count quota or age quota get removed
            to_remove: List[Path] = []
            while len(slots) - len(to_remove) > max_slots_per_project:
                to_remove.append(slots[len(to_remove)][0])

            for slot_dir, access_time in slots:
                if slot_dir not in to_remove and (now - access_time) > max_age_seconds:
                    to_remove.append(slot_dir)

            for target in to_remove:
                try:
                    await asyncio.to_thread(shutil.rmtree, target, True)
                    pruned_count += 1
                except Exception:
                    pass

        return pruned_count

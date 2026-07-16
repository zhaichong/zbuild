# -*- coding: utf-8 -*-
"""Build cache with content-hash deduplication.

Inspired by Turborepo's caching strategy: computes a hash of the
input files (commit SHA + deploy.sh + package.json) and uses it
to skip redundant rebuilds.
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Optional

from core.constants import APP_DIR
from git.build import get_commit_sha

logger = logging.getLogger(__name__)

CACHE_DIR = APP_DIR / "tmp" / "build-cache"


class BuildCache:
    """Content-hash based build cache.

    The cache key is a SHA-256 hash of:
    - Current commit SHA
    - deploy.sh contents
    - package.json contents
    - Lock file contents (if present)

    Cached artifacts are stored in ``CACHE_DIR/{hash}/``.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Hash computation
    # ------------------------------------------------------------------

    def compute_input_hash(self, project_path: Path | str) -> str:
        """Compute a content hash from the project's build inputs.

        Combines commit SHA, deploy.sh, package.json, and lock file
        into a single SHA-256 hash.
        """
        project = Path(project_path)
        h = hashlib.sha256()

        # Commit SHA
        sha = get_commit_sha(project)
        h.update(f"commit:{sha}\n".encode())

        # deploy.sh
        deploy_sh = project / "deploy.sh"
        if deploy_sh.is_file():
            h.update(f"deploy.sh:{deploy_sh.stat().st_size}\n".encode())
            h.update(deploy_sh.read_bytes())
            h.update(b"\n")

        # package.json
        pkg_json = project / "package.json"
        if pkg_json.is_file():
            h.update(f"package.json:{pkg_json.stat().st_size}\n".encode())
            h.update(pkg_json.read_bytes())
            h.update(b"\n")

        # Lock file (try multiple names)
        for lock_name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"):
            lock_file = project / lock_name
            if lock_file.is_file():
                h.update(f"{lock_name}:{lock_file.stat().st_size}\n".encode())
                h.update(lock_file.read_bytes())
                h.update(b"\n")
                break

        return h.hexdigest()

    # ------------------------------------------------------------------
    # Cache operations
    # ------------------------------------------------------------------

    def get_cached_artifact(self, input_hash: str) -> Optional[Path]:
        """Return the cached artifact path if it exists, or None."""
        artifact_dir = self.cache_dir / input_hash
        if not artifact_dir.is_dir():
            return None

        tarballs = list(artifact_dir.glob("*.tar.gz"))
        if tarballs:
            logger.info("Cache hit for %s", input_hash[:12])
            return tarballs[0]

        return None

    def store_artifact(self, input_hash: str, artifact_path: Path) -> Path:
        """Store an artifact in the cache.

        Returns the path to the cached copy.
        """
        artifact_dir = self.cache_dir / input_hash
        artifact_dir.mkdir(parents=True, exist_ok=True)

        dest = artifact_dir / artifact_path.name
        if not dest.exists():
            shutil.copy2(str(artifact_path), str(dest))
            logger.info("Cached artifact: %s -> %s", artifact_path.name, input_hash[:12])

        # Store metadata
        meta = {
            "input_hash": input_hash,
            "artifact_name": artifact_path.name,
            "size_bytes": artifact_path.stat().st_size,
        }
        meta_path = artifact_dir / "cache-meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        return dest

    def has_cache(self, input_hash: str) -> bool:
        """Return True if a cached artifact exists for this hash."""
        return self.get_cached_artifact(input_hash) is not None

    def clear(self) -> int:
        """Remove all cached artifacts. Returns the number of entries removed."""
        count = 0
        for entry in self.cache_dir.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
                count += 1
        logger.info("Cache cleared: %d entries removed", count)
        return count

# -*- coding: utf-8 -*-
"""Tests for multi-version dependency fingerprint cache and workspace linking."""

import asyncio
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from git.deps import (
    dependency_fingerprint,
    compute_deps_slot_key,
    dependency_install_command,
)
from server.workspace import WorkspaceManager, _create_dir_link, _remove_dir_link


class TestDepsCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.project_a = self.root / "projects" / "app-a"
        self.project_a.mkdir(parents=True)
        (self.project_a / "package.json").write_text('{"name": "app-a", "dependencies": {"vue": "^2.6.14"}}', encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dependency_fingerprint_and_slot_key(self):
        # 1. Compute initial fingerprint and slot key
        fp1 = dependency_fingerprint(self.project_a)
        key1 = compute_deps_slot_key(self.project_a)
        self.assertTrue(len(key1) == 16)

        # Same dependencies yield identical slot key
        self.assertEqual(compute_deps_slot_key(self.project_a), key1)

        # 2. Modify package.json to simulate dependency version change (e.g. branch checkout)
        (self.project_a / "package.json").write_text('{"name": "app-a", "dependencies": {"vue": "^3.0.0"}}', encoding="utf-8")
        fp2 = dependency_fingerprint(self.project_a)
        key2 = compute_deps_slot_key(self.project_a)

        self.assertNotEqual(fp1, fp2)
        self.assertNotEqual(key1, key2)
        self.assertTrue(len(key2) == 16)

    def test_install_command_contains_offline_flags(self):
        cmd = dependency_install_command(self.project_a)
        # Verify offline / performance optimizations are passed
        self.assertTrue(any("--prefer-offline" in arg for arg in cmd))

    def test_dir_link_creation_and_removal(self):
        src_cache = self.root / "deps_cache" / "slot1" / "node_modules"
        src_cache.mkdir(parents=True)
        (src_cache / "fake_pkg.txt").write_text("hello-package", encoding="utf-8")

        target_link = self.root / "worktree" / "node_modules"
        target_link.parent.mkdir(parents=True, exist_ok=True)

        _create_dir_link(target_link, src_cache)
        self.assertTrue(target_link.exists())
        self.assertTrue((target_link / "fake_pkg.txt").exists())
        self.assertEqual((target_link / "fake_pkg.txt").read_text(encoding="utf-8"), "hello-package")

        # Removing link should not delete the underlying cache
        _remove_dir_link(target_link)
        self.assertFalse(target_link.exists())
        self.assertTrue(src_cache.exists())
        self.assertTrue((src_cache / "fake_pkg.txt").exists())

    def test_prune_deps_cache_lru(self):
        async def run_lru():
            ws = WorkspaceManager(self.root / "data", {})
            cache_root = ws.deps_cache_root / "test-proj"
            cache_root.mkdir(parents=True)

            # Create 6 slots with different access times
            for i in range(6):
                slot = cache_root / f"slot_{i}"
                slot.mkdir(parents=True)
                (slot / ".last_accessed").write_text(str(1000 + i * 10), encoding="utf-8")

            # Prune keeping max 3 slots
            pruned = await ws.prune_deps_cache(max_slots_per_project=3, max_age_seconds=999999)
            self.assertEqual(pruned, 3)

            # Oldest slots (0, 1, 2) should be removed, newest (3, 4, 5) kept
            remaining = sorted([p.name for p in cache_root.iterdir() if p.is_dir()])
            self.assertEqual(remaining, ["slot_3", "slot_4", "slot_5"])

        asyncio.run(run_lru())


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from git.branches import ensure_branch, local_changes_summary, read_current_branch
from core.history import HistoryStore
from workflow.pipeline import Pipeline
from workflow.step_fns import step_switch_branch
from workflow.step_fns import step_check_tools
from workflow.steps import StepContext, StepDefinition, StepResult
from typing import List


def _git(repo: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


class TestPipelineBranchRestore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "project"
        self.repo.mkdir()
        _git(self.repo, "init", "-b", "main")
        _git(self.repo, "config", "user.email", "test@example.com")
        _git(self.repo, "config", "user.name", "Test")
        (self.repo / "file.txt").write_text("main", encoding="utf-8")
        _git(self.repo, "add", "file.txt")
        _git(self.repo, "commit", "-m", "initial")
        _git(self.repo, "branch", "feature")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run(self, final_success: bool, allow_stash: bool = False, restore_branch: bool = False):
        pipeline = Pipeline.__new__(Pipeline)
        pipeline.mode = "local"
        pipeline.config = {"allow_stash": allow_stash, "restore_branch": restore_branch}
        final_step = StepDefinition(
            name="final",
            fn=lambda _ctx: StepResult(success=final_success, message="final"),
        )
        steps = [StepDefinition(name="switch", fn=step_switch_branch), final_step]
        with patch("workflow.pipeline.get_steps", return_value=steps):
            return pipeline.run_one({
                "name": "project",
                "path": str(self.repo),
                "branch": "feature",
            })

    def test_stays_on_switched_branch_by_default_after_success(self):
        result = self._run(final_success=True, restore_branch=False)
        self.assertTrue(result.success)
        self.assertEqual(read_current_branch(self.repo), "feature")

    def test_stays_on_switched_branch_by_default_after_failure(self):
        result = self._run(final_success=False, restore_branch=False)
        self.assertFalse(result.success)
        self.assertEqual(read_current_branch(self.repo), "feature")

    def test_restores_original_branch_when_configured(self):
        result = self._run(final_success=True, restore_branch=True)
        self.assertTrue(result.success)
        self.assertEqual(read_current_branch(self.repo), "main")

    def test_restores_current_changes_when_configured(self):
        (self.repo / "file.txt").write_text("older-stash", encoding="utf-8")
        _git(self.repo, "stash", "push", "-m", "existing-user-stash")
        (self.repo / "file.txt").write_text("current-change", encoding="utf-8")

        result = self._run(final_success=True, allow_stash=True, restore_branch=True)

        self.assertTrue(result.success)
        self.assertEqual(read_current_branch(self.repo), "main")
        self.assertEqual((self.repo / "file.txt").read_text(encoding="utf-8"), "current-change")
        stash_list = subprocess.run(
            ["git", "stash", "list"], cwd=self.repo, text=True, capture_output=True, check=True
        ).stdout
        self.assertIn("existing-user-stash", stash_list)
        self.assertNotIn("zbuild-auto-stash", stash_list)

    def test_reports_failure_when_stashed_changes_cannot_be_restored(self):
        (self.repo / "file.txt").write_text("current-change", encoding="utf-8")
        from tools.exec import run_process as real_run_process

        def fail_stash_pop(args, **kwargs):
            if list(args)[-2:] == ["stash", "pop"]:
                return subprocess.CompletedProcess(args, 1, "", "conflict")
            return real_run_process(args, **kwargs)

        with patch("tools.exec.run_process", side_effect=fail_stash_pop):
            result = self._run(final_success=True, allow_stash=True, restore_branch=True)

        self.assertFalse(result.success)
        self.assertIn("恢复", result.error_message)


    def test_does_not_switch_branch_when_stash_fails(self):
        (self.repo / 'file.txt').write_text('current-change', encoding='utf-8')

        with patch('git.branches.stash_local_changes', return_value=False):
            result = ensure_branch(self.repo, 'feature', allow_stash=True)

        self.assertFalse(result)
        self.assertEqual(read_current_branch(self.repo), 'main')


class TestLocalChanges(unittest.TestCase):
    def test_unmerged_file_is_reported_as_dirty(self):
        git_status = subprocess.CompletedProcess([], 0, 'UU conflict.txt\n', '')

        with patch('git.branches.run_process', return_value=git_status):
            summary = local_changes_summary(Path('C:/project'))

        self.assertTrue(summary['has_changes'])
        self.assertEqual(summary['staged'], ['conflict.txt'])


class TestPipelineValidation(unittest.TestCase):
    def _pipeline(self, mode: str, **config):
        pipeline = Pipeline.__new__(Pipeline)
        pipeline.mode = mode
        pipeline.config = {
            "mode": mode,
            "projects": [{"name": "project", "path": "C:/project", "enabled": True}],
            **config,
        }
        return pipeline

    def test_server_requires_upload_path_for_every_project(self):
        pipeline = self._pipeline(
            "server",
            server={"host": "server", "username": "user", "password": "secret"},
        )
        with self.assertRaisesRegex(ValueError, "upload path"):
            pipeline._validate_payload()

    def test_svn_requires_hospital_and_order(self):
        pipeline = self._pipeline(
            "svn",
            svn_root="https://svn.example/repo",
            svn_credentials={"username": "user", "password": "secret"},
        )
        with self.assertRaisesRegex(ValueError, "hospital_name"):
            pipeline._validate_payload()

    def test_server_mode_checks_paramiko_before_building(self):
        ctx = StepContext(
            project_name="project",
            project_path=Path("C:/project"),
            branch="main",
            mode="server",
            config={},
        )
        detected = {
            "git": {"path": "git"},
            "bash": {"path": "bash"},
            "svn": {"path": ""},
            "node": {"path": ""},
        }
        with patch("tools.detect.detect_tools", return_value=detected), patch(
            "importlib.util.find_spec", return_value=None
        ):
            result = step_check_tools(ctx)

        self.assertFalse(result.success)
        self.assertIn("paramiko", result.message)


    def test_requires_at_least_one_enabled_project(self):
        pipeline = self._pipeline('local')
        pipeline.config['projects'][0]['enabled'] = False

        with self.assertRaisesRegex(ValueError, 'enabled'):
            pipeline._validate_payload()


class TestMultiProjectPipeline(unittest.TestCase):
    def test_runs_all_enabled_projects_and_records_each_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            projects = []
            for name in ("project-a", "project-b"):
                project_path = root / name
                project_path.mkdir()
                projects.append({"name": name, "path": str(project_path), "enabled": True})

            uploaded: List[str] = []

            def build(ctx):
                artifact = ctx.project_path / "dist" / f"{ctx.project_name}.tar.gz"
                artifact.parent.mkdir()
                artifact.write_bytes(ctx.project_name.encode())
                ctx.artifact_path = artifact
                return StepResult(True, "built", {"artifact_path": str(artifact)})

            def upload(ctx):
                uploaded.append(ctx.project_name)
                return StepResult(True, "uploaded", {"target_url": f"local://{ctx.project_name}"})

            pipeline = Pipeline.__new__(Pipeline)
            pipeline.payload = {}
            pipeline.mode = "local"
            pipeline.config = {"mode": "local", "projects": projects}
            pipeline.history_store = HistoryStore(root / "history")
            steps = [StepDefinition("build", build), StepDefinition("upload", upload)]

            with patch("workflow.pipeline.get_steps", return_value=steps):
                result = pipeline.run()

            self.assertTrue(result.success)
            self.assertEqual(sorted(uploaded), ["project-a", "project-b"])
            # Records keep submission order even when projects run in parallel
            self.assertEqual([item.project_name for item in result.projects], ["project-a", "project-b"])
            self.assertTrue(all(item.artifact and item.artifact.size_bytes > 0 for item in result.projects))

    def test_failed_build_is_not_uploaded_and_next_project_continues(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            projects = []
            for name in ("broken", "healthy"):
                project_path = root / name
                project_path.mkdir()
                projects.append({"name": name, "path": str(project_path), "enabled": True})

            uploaded: List[str] = []

            def build(ctx):
                if ctx.project_name == "broken":
                    return StepResult(False, "build failed")
                artifact = ctx.project_path / "dist" / "healthy.tar.gz"
                artifact.parent.mkdir()
                artifact.write_bytes(b"healthy")
                ctx.artifact_path = artifact
                return StepResult(True, "built", {"artifact_path": str(artifact)})

            def upload(ctx):
                uploaded.append(ctx.project_name)
                return StepResult(True, "uploaded")

            pipeline = Pipeline.__new__(Pipeline)
            pipeline.payload = {}
            pipeline.mode = "local"
            pipeline.config = {"mode": "local", "projects": projects}
            pipeline.history_store = HistoryStore(root / "history")
            steps = [StepDefinition("build", build), StepDefinition("upload", upload)]

            with patch("workflow.pipeline.get_steps", return_value=steps):
                result = pipeline.run()

            self.assertFalse(result.success)
            self.assertEqual(uploaded, ["healthy"])
            self.assertEqual([item.success for item in result.projects], [False, True])


class TestParallelPipeline(unittest.TestCase):
    """Parallel multi-project execution (max_concurrent)."""

    def setUp(self):
        self._temp_dirs = []

    def tearDown(self):
        for temp_dir in self._temp_dirs:
            temp_dir.cleanup()

    def _pipeline(self, projects, max_concurrent: int):
        temp_dir = tempfile.TemporaryDirectory()
        self._temp_dirs.append(temp_dir)
        root = Path(temp_dir.name)
        for name in projects:
            (root / name).mkdir()
        config = {
            "mode": "local",
            "max_concurrent": max_concurrent,
            "projects": [
                {"name": name, "path": str(root / name), "enabled": True}
                for name in projects
            ],
        }
        pipeline = Pipeline.__new__(Pipeline)
        pipeline.payload = {}
        pipeline.mode = "local"
        pipeline.config = config
        pipeline.history_store = HistoryStore(root / "history")
        return pipeline

    def test_projects_overlap_when_max_concurrent_gt_1(self):
        events = []  # (name, 'start'|'end', timestamp)
        import time as _time

        def build(ctx):
            events.append((ctx.project_name, "start", _time.time()))
            _time.sleep(0.4)
            events.append((ctx.project_name, "end", _time.time()))
            artifact = ctx.project_path / "dist" / f"{ctx.project_name}.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(ctx.project_name.encode())
            ctx.artifact_path = artifact
            return StepResult(True, "built", {"artifact_path": str(artifact)})

        def upload(ctx):
            return StepResult(True, "uploaded")

        pipeline = self._pipeline(["project-a", "project-b"], max_concurrent=2)
        steps = [StepDefinition("build", build), StepDefinition("upload", upload)]

        with patch("workflow.pipeline.get_steps", return_value=steps):
            result = pipeline.run()

        self.assertTrue(result.success)
        start_a = next(t for n, k, t in events if n == "project-a" and k == "start")
        end_a = next(t for n, k, t in events if n == "project-a" and k == "end")
        start_b = next(t for n, k, t in events if n == "project-b" and k == "start")
        # Both builds must have overlapped (b started before a finished)
        self.assertLess(start_b, end_a, "projects should run concurrently with max_concurrent=2")
        self.assertLess(start_a, end_a)

    def test_serial_when_max_concurrent_is_1(self):
        events = []
        import time as _time

        def build(ctx):
            events.append((ctx.project_name, "start", _time.time()))
            _time.sleep(0.1)
            events.append((ctx.project_name, "end", _time.time()))
            artifact = ctx.project_path / "dist" / f"{ctx.project_name}.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(ctx.project_name.encode())
            ctx.artifact_path = artifact
            return StepResult(True, "built", {"artifact_path": str(artifact)})

        def upload(ctx):
            return StepResult(True, "uploaded")

        pipeline = self._pipeline(["project-a", "project-b"], max_concurrent=1)
        steps = [StepDefinition("build", build), StepDefinition("upload", upload)]

        with patch("workflow.pipeline.get_steps", return_value=steps):
            result = pipeline.run()

        self.assertTrue(result.success)
        start_a = next(t for n, k, t in events if n == "project-a" and k == "start")
        end_a = next(t for n, k, t in events if n == "project-a" and k == "end")
        start_b = next(t for n, k, t in events if n == "project-b" and k == "start")
        self.assertGreaterEqual(start_b, end_a, "max_concurrent=1 must run projects serially")

    def test_exception_in_one_project_does_not_hide_others(self):
        uploaded = []

        def build(ctx):
            artifact = ctx.project_path / "dist" / f"{ctx.project_name}.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(ctx.project_name.encode())
            ctx.artifact_path = artifact
            return StepResult(True, "built", {"artifact_path": str(artifact)})

        def upload(ctx):
            uploaded.append(ctx.project_name)
            return StepResult(True, "uploaded")

        pipeline = self._pipeline(["broken", "healthy"], max_concurrent=2)
        steps = [StepDefinition("build", build), StepDefinition("upload", upload)]
        original_run_one = Pipeline.run_one

        def exploding_run_one(self, proj_config):
            if proj_config["name"] == "broken":
                raise RuntimeError("boom")
            return original_run_one(self, proj_config)

        with patch("workflow.pipeline.get_steps", return_value=steps), patch.object(
            Pipeline, "run_one", exploding_run_one
        ):
            result = pipeline.run()

        self.assertFalse(result.success)
        self.assertEqual([p.project_name for p in result.projects], ["broken", "healthy"])
        self.assertEqual([p.success for p in result.projects], [False, True])
        self.assertIn("boom", result.projects[0].error_message)
        self.assertEqual(uploaded, ["healthy"])


if __name__ == "__main__":
    unittest.main()

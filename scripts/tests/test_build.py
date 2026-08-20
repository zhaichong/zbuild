# -*- coding: utf-8 -*-

import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.errors import BuildError
from git.build import build_project, is_ignorable_tar_stat_failure
from workflow.step_fns import step_build
from workflow.steps import StepContext, StepResult


class TestBuildFailure(unittest.TestCase):
    def test_build_passes_target_branch_to_shell_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "deploy.sh").write_text("exit 0", encoding="utf-8")
            artifact = project / "dist" / "app.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(b"artifact")
            completed = subprocess.CompletedProcess(["bash", "deploy.sh"], 0, "", "")

            with patch("git.build.run_process_stream", return_value=completed) as run, patch(
                "git.build.latest_changed_artifact", return_value=artifact
            ):
                build_project(project, target_branch="release-hospital")

            self.assertEqual(run.call_args.args[0], ["bash", "deploy.sh", "release-hospital"])

    def test_build_uses_isolated_node14_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "deploy.sh").write_text("exit 1", encoding="utf-8")
            expected_env = {"PATH": "node14-shims;system-path", "NPM_CONFIG_PREFIX": "isolated"}
            failed = subprocess.CompletedProcess(["bash", "deploy.sh"], 1, "failed", "")

            with patch("git.deps._node_env", return_value=expected_env), patch(
                "git.build.run_process_stream", return_value=failed
            ) as mock_run:
                with self.assertRaises(BuildError):
                    build_project(project)

            self.assertEqual(mock_run.call_args.kwargs["env"], expected_env)

    def test_nonzero_build_is_failure_even_when_artifact_was_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "deploy.sh").write_text("exit 1", encoding="utf-8")
            artifact = project / "dist" / "broken.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(b"partial")
            failed = subprocess.CompletedProcess(["bash", "deploy.sh"], 1, "partial output", "")

            with patch("git.build.run_process_stream", return_value=failed), patch(
                "git.build.latest_changed_artifact", return_value=artifact
            ):
                with self.assertRaises(BuildError):
                    build_project(project)

    def test_ignores_only_known_tar_stat_failure_with_readable_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "dist" / "bedhead-3.1.4.tar.gz"
            artifact.parent.mkdir()
            with tarfile.open(artifact, "w") as archive:
                info = tarfile.TarInfo("bedhead/index.html")
                info.size = 0
                archive.addfile(info)

            result = subprocess.CompletedProcess(
                ["bash", "deploy.sh"],
                2,
                "tar: 3.1.4_hospital_202608131353: Cannot stat: No such file or directory\n"
                "tar: Exiting with failure status due to previous errors",
                "",
            )

            self.assertTrue(is_ignorable_tar_stat_failure(result, artifact))
            (Path(temp_dir) / "deploy.sh").write_text("exit 2\n", encoding="utf-8")
            with patch("git.build.run_process_stream", return_value=result), patch(
                "git.build.latest_changed_artifact", return_value=artifact
            ), patch("git.build.logger") as mock_logger:
                _, selected = build_project(Path(temp_dir))

            self.assertEqual(selected, artifact)
            self.assertIn(
                "Ignoring known non-fatal tar missing-path error",
                mock_logger.info.call_args_list[-1].args[0],
            )

    def test_does_not_ignore_other_tar_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "dist" / "broken.tar.gz"
            artifact.parent.mkdir()
            artifact.write_bytes(b"not an archive")
            result = subprocess.CompletedProcess(
                ["bash", "deploy.sh"],
                2,
                "tar: bedhead: Cannot open: Permission denied\n"
                "tar: Exiting with failure status due to previous errors",
                "",
            )

            self.assertFalse(is_ignorable_tar_stat_failure(result, artifact))

    def test_step_build_uses_custom_build_command(self):
        ctx = StepContext(
            project_name="custom-proj",
            project_path=Path("/dummy/path"),
            branch="master",
            mode="local",
            config={"buildCommand": "npm run build:prod"},
            tools={"bash": "bash"},
            extra={"build_command": "npm run build:prod"},
        )

        completed = subprocess.CompletedProcess(["npm", "run", "build:prod"], 0, "ok", "")
        artifact = Path("/dummy/path/dist/app.tar.gz")
        with patch("git.build.build_project", return_value=(completed, artifact)) as mock_build:
            result = step_build(ctx)
            self.assertTrue(result.success)
            self.assertEqual(ctx.artifact_path, artifact)
            self.assertEqual(mock_build.call_args.kwargs["build_command"], "npm run build:prod")


if __name__ == "__main__":
    unittest.main()

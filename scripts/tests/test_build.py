# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.errors import BuildError
from git.build import build_project
from workflow.step_fns import step_build
from workflow.steps import StepContext, StepResult


class TestBuildFailure(unittest.TestCase):
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

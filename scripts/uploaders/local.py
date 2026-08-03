# -*- coding: utf-8 -*-
"""Local uploader (Buildkite plugin pattern).

Simply copies the artifact to a local output directory.
"""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path
from typing import Any

from core.constants import APP_DIR
from uploaders.base import BaseUploader, UploadResult, as_log_fn


class LocalUploader(BaseUploader):
    """Copy artifacts to a local output directory.

    Configuration keys used:
    - ``local_output``: target directory path (default: ``<APP_DIR>/local-output``)
    """

    max_retries = 0

    def upload(
        self,
        artifact: Path,
        config: dict[str, Any],
        log: Any = None,
        project_name: str = "",
    ) -> UploadResult:
        log_fn = as_log_fn(log)
        output_dir = Path(config.get("local_output", str(APP_DIR / "local-output")))
        output_dir.mkdir(parents=True, exist_ok=True)

        dest = output_dir / artifact.name
        file_size = artifact.stat().st_size
        start_time = time.time()

        log_fn(f"正在复制产物到本地目录: {artifact.name} -> {dest}")

        try:
            shutil.copy2(str(artifact), str(dest))

            duration = time.time() - start_time
            return UploadResult(
                success=True,
                target_url=str(dest),
                message=f"已复制到: {dest}",
                bytes_uploaded=file_size,
                duration_seconds=duration,
            )
        except Exception as exc:
            return UploadResult(
                success=False,
                target_url=str(dest),
                message=f"本地复制失败: {exc}",
                duration_seconds=time.time() - start_time,
            )

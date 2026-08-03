# -*- coding: utf-8 -*-
"""Abstract base uploader (Buildkite plugin pattern).

All uploaders (SVN, Server, Local) inherit from ``BaseUploader``
and implement the ``upload`` method.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


def as_log_fn(log: Any) -> Callable[[str], None]:
    """Normalize a logger or callable into a single-argument log function."""
    if log is None:
        return lambda msg: None
    if callable(log):
        return log
    info = getattr(log, "info", None)
    if callable(info):
        return lambda msg: info("%s", msg)
    return lambda msg: None


@dataclass
class UploadResult:
    """Result of an upload operation."""
    success: bool
    target_url: str = ""
    message: str = ""
    bytes_uploaded: int = 0
    duration_seconds: float = 0.0


class BaseUploader(ABC):
    """Abstract base class for artifact uploaders.

    Subclasses must implement ``upload()`` and may override
    ``max_retries`` to control retry behaviour.

    Attributes
    ----------
    max_retries:
        Maximum number of retry attempts on transient failures.
    """

    max_retries: int = 0

    @abstractmethod
    def upload(
        self,
        artifact: Path,
        config: dict[str, Any],
        log: logging.Logger,
        project_name: str = "",
    ) -> UploadResult:
        """Upload an artifact to the destination.

        Parameters
        ----------
        artifact:
            Path to the artifact file (typically a .tar.gz).
        config:
            The full tool configuration dict.
        log:
            Logger instance for emitting progress messages.
        project_name:
            Name of the project being uploaded, used to look up
            project-specific settings from config['projects'].

        Returns
        -------
        UploadResult:
            Outcome of the upload operation.
        """
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} max_retries={self.max_retries}>"

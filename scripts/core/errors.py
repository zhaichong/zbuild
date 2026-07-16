# -*- coding: utf-8 -*-
"""Structured exception hierarchy for zbuild."""


class ToolError(Exception):
    """Base class for all zbuild errors.

    All custom exceptions in the tool inherit from this class so that
    callers can catch ``ToolError`` to handle any known failure uniformly.
    """


class InternalError(ToolError):
    """Unexpected internal failure.

    Raised when an invariant is violated or an unhandled edge case is
    reached.  These bugs should be reported and fixed.
    """


class ConfigError(ToolError):
    """Invalid or missing configuration.

    Raised when required configuration files are absent, malformed, or
    contain values that fail validation.
    """


class UploadError(ToolError):
    """Artifact upload failure (SVN / server / local).

    Raised by any uploader (SVN, SSH/SFTP, local copy) when the artifact
    cannot be delivered to its destination after all retries are exhausted.
    """


class BuildError(ToolError):
    """Build / packaging failure.

    Raised when deploy.sh or a dependency install step fails.
    """


class GitError(ToolError):
    """Git operation failure.

    Raised when branch switching, pulling, or other git commands fail.
    """


class DependencyError(ToolError):
    """Missing external tool or runtime.

    Raised when a required executable (git, bash, svn, node, etc.)
    cannot be found on the system.
    """

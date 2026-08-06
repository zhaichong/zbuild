# -*- coding: utf-8 -*-
"""Subprocess execution helpers.

Provides ``run_process`` for one-shot commands and ``run_process_stream``
for commands whose stdout/stderr should be forwarded line-by-line.
"""

import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

_SECRET_FLAGS = {"--password", "--secret", "--token", "--api-key", "--api_key"}


def _redacted_args(args: Sequence[str]) -> List[str]:
    """Return command arguments safe for diagnostic logging."""
    redacted: List[str] = []
    hide_next = False
    for value in args:
        text = str(value)
        lower = text.lower()
        if hide_next:
            redacted.append("***")
            hide_next = False
            continue
        if lower in _SECRET_FLAGS:
            redacted.append(text)
            hide_next = True
            continue
        matched = next((flag for flag in _SECRET_FLAGS if lower.startswith(flag + "=")), None)
        redacted.append(text.split("=", 1)[0] + "=***" if matched else text)
    return redacted


def _startupinfo():
    """Return a STARTUPINFO object to hide console windows on Windows."""
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def run_process(
    args: Sequence[str],
    *,
    cwd: Union[Path, str, None] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process.

    Parameters
    ----------
    args:
        Command and arguments.
    cwd:
        Working directory for the subprocess.
    env:
        Extra environment variables (merged with the current environ).
    timeout:
        Seconds before the process is killed.
    encoding:
        Text encoding for stdout/stderr.
    check:
        If True, raise ``subprocess.CalledProcessError`` on non-zero exit.
    """
    import os
    merged_env = None
    if env:
        merged_env = {**os.environ, **env}

    logger.debug("run_process: %s (cwd=%s)", _redacted_args(args), cwd)
    result = subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        capture_output=True,
        text=True,
        encoding=encoding,
        errors="replace",
        timeout=timeout,
        startupinfo=_startupinfo(),
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, args, result.stdout, result.stderr
        )
    return result


def run_process_stream(
    args: Sequence[str],
    *,
    cwd: Union[Path, str, None] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
    on_line: Optional[Callable[[str], None]] = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command, streaming stdout line-by-line.

    Each line is passed to *on_line* (if provided) and also collected
    into the returned CompletedProcess.

    Parameters
    ----------
    args:
        Command and arguments.
    cwd:
        Working directory for the subprocess.
    env:
        Extra environment variables (merged with the current environ).
    timeout:
        Seconds before the process is killed.
    encoding:
        Text encoding for stdout/stderr.
    on_line:
        Callback invoked for each stdout line (without trailing newline).
    check:
        If True, raise ``subprocess.CalledProcessError`` on non-zero exit.
    """
    import os
    merged_env = None
    if env:
        merged_env = {**os.environ, **env}

    logger.debug("run_process_stream: %s (cwd=%s)", _redacted_args(args), cwd)

    proc = subprocess.Popen(
        list(args),
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=encoding,
        errors="replace",
        startupinfo=_startupinfo(),
    )

    lines: List[str] = []

    def _reader():
        assert proc.stdout is not None
        for line in proc.stdout:
            stripped = line.rstrip("\n\r")
            lines.append(stripped)
            if on_line:
                try:
                    on_line(stripped)
                except Exception:
                    logger.exception("on_line callback error")

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        reader_thread.join(timeout=5)
        raise

    reader_thread.join(timeout=10)
    stdout_text = "\n".join(lines)

    result = subprocess.CompletedProcess(
        args=list(args),
        returncode=proc.returncode,
        stdout=stdout_text,
        stderr="",
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, args, result.stdout, result.stderr
        )
    return result

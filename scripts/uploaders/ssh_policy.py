# -*- coding: utf-8 -*-
"""SSH host-key policy helpers.

Default: load system + app-local known_hosts; unknown hosts are accepted once
and persisted under DATA_DIR/ssh_known_hosts (TOFU — trust on first use).

Strict mode (``ZBUILD_SSH_STRICT=1``): reject unknown hosts entirely.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from core.constants import DATA_DIR

logger = logging.getLogger(__name__)

KNOWN_HOSTS_NAME = "ssh_known_hosts"


def known_hosts_path() -> Path:
    return Path(DATA_DIR) / KNOWN_HOSTS_NAME


def open_ssh_client(paramiko_mod: Optional[Any] = None):
    """Create a configured ``paramiko.SSHClient``.

    Parameters
    ----------
    paramiko_mod:
        Optional pre-imported paramiko module (tests inject a fake).
    """
    if paramiko_mod is None:
        import paramiko as paramiko_mod  # type: ignore

    client = paramiko_mod.SSHClient()

    # System known_hosts (~/.ssh/known_hosts)
    try:
        client.load_system_host_keys()
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.debug("load_system_host_keys failed: %s", exc)

    kh = known_hosts_path()
    if kh.exists():
        try:
            client.load_host_keys(str(kh))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load app known_hosts %s: %s", kh, exc)

    strict = os.environ.get("ZBUILD_SSH_STRICT", "").strip() in {"1", "true", "yes"}
    if strict:
        client.set_missing_host_key_policy(paramiko_mod.RejectPolicy())
        return client

    base_policy = getattr(paramiko_mod, "MissingHostKeyPolicy", object)

    class PersistUnknownHostKey(base_policy):  # type: ignore[misc,valid-type]
        """TOFU: accept unknown key once and persist to app known_hosts."""

        def missing_host_key(self, client_obj, hostname, key):  # noqa: ANN001
            client_obj.get_host_keys().add(hostname, key.get_name(), key)
            path = known_hosts_path()
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                client_obj.save_host_keys(str(path))
                logger.info("Trusted new SSH host key for %s (saved to %s)", hostname, path)
            except OSError as exc:
                logger.warning("Could not persist host key for %s: %s", hostname, exc)

    client.set_missing_host_key_policy(PersistUnknownHostKey())
    return client

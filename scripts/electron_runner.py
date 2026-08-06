# -*- coding: utf-8 -*-
"""Slim entry point for the Electron-spawned Python process.

This script is launched by the Electron frontend as a child process.
It sets up ``sys.path``, imports the command registry, and delegates
to ``runner.cli.main()`` which dispatches to the appropriate command.

Usage (from Electron)::

    python scripts/electron_runner.py <command-name>

The command receives a JSON payload on stdin and emits JSON events
on stdout (see ``runner.protocol``).
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: ensure the scripts/ directory is on sys.path so that
# ``import core.*``, ``import runner.*``, etc. all resolve correctly.
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Node.js OpenSSL compatibility check for Node.js 17+
# ---------------------------------------------------------------------------
def _setup_node_openssl_compat():
    # Clean any inherited --openssl-legacy-provider from NODE_OPTIONS
    # as Node 14 does not support this flag and will abort immediately.
    node_opts = os.environ.get("NODE_OPTIONS", "")
    if "--openssl-legacy-provider" in node_opts:
        os.environ["NODE_OPTIONS"] = " ".join(f for f in node_opts.split() if f != "--openssl-legacy-provider")

_setup_node_openssl_compat()

# ---------------------------------------------------------------------------
# Import all command modules to populate the @register registry.
# This must happen before cli.main() is called.
# ---------------------------------------------------------------------------

import runner.commands  # noqa: F401  (triggers @register decorators)

# ---------------------------------------------------------------------------
# Delegate to the CLI dispatcher
# ---------------------------------------------------------------------------

from runner.cli import main  # noqa: E402

if __name__ == "__main__":
    main()

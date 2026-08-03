# -*- coding: utf-8 -*-
"""Import all command modules to trigger @register decorators.

This package __init__ ensures that every command module is imported
when ``runner.commands`` is imported, which populates the command
registry in ``runner.cli``.
"""

from runner.commands import (  # noqa: F401
    config_cmd,
    detect_cmd,
    discover_cmd,
    svn_cmd,
    server_cmd,
    run_cmd,
    history_cmd,
    template_cmd,
    affected_cmd,
    order_dir_cmd,
)

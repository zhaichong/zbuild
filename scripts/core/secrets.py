# -*- coding: utf-8 -*-
"""Helpers for stripping credentials from persisted JSON structures."""

from typing import Any

# Keys (case-insensitive) whose values must never be written to disk snapshots.
_SECRET_KEYS = frozenset({
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
})


def without_secrets(value: Any) -> Any:
    """Return a JSON-safe deep copy with credential fields removed.

    Nested dicts/lists are walked. Dict keys matching known secret names
    (case-insensitive) are dropped entirely so templates, history, and
    debug dumps never retain passwords.
    """
    if isinstance(value, dict):
        return {
            key: without_secrets(item)
            for key, item in value.items()
            if str(key).lower() not in _SECRET_KEYS
        }
    if isinstance(value, list):
        return [without_secrets(item) for item in value]
    if isinstance(value, tuple):
        return [without_secrets(item) for item in value]
    return value

# -*- coding: utf-8 -*-
"""Per-browser profile persistence for the LAN Web interface.

Profiles are deliberately not user accounts.  The opaque id comes from a
HttpOnly browser cookie and is only used to keep one browser's preferences,
SVN credentials, and task history separate from another browser's.
"""

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from server.secrets import (
    DpapiSecretCodec,
    SECRET_MARKER,
    SecretCodec,
    decrypt_secret_json,
    encrypt_secret_json,
    merge_secrets,
    split_secrets,
)


class ProfileConflict(RuntimeError):
    pass


class ProfileStore:
    """Stores public profile preferences and encrypted secrets separately."""

    def __init__(self, data_dir: Path, codec: Optional[SecretCodec] = None):
        self.path = Path(data_dir).resolve() / "profiles.db"
        self.codec = codec or DpapiSecretCodec()
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        with self._db:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS profiles (
                    profile_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL DEFAULT '{}',
                    secret_ciphertext TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _revision(public: Dict[str, Any], ciphertext: str) -> str:
        raw = json.dumps(public, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256((raw + "\n" + ciphertext).encode("utf-8")).hexdigest()

    def _row(self, profile_id: str):
        return self._db.execute(
            "SELECT * FROM profiles WHERE profile_id=?", (profile_id,)
        ).fetchone()

    def _values(self, profile_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        row = self._row(profile_id)
        if not row:
            return {}, {}, "0"
        public = json.loads(row["config_json"])
        secrets = decrypt_secret_json(self.codec, row["secret_ciphertext"])
        return public, secrets, self._revision(public, row["secret_ciphertext"])

    def get_public(self, profile_id: str) -> Dict[str, Any]:
        with self._lock:
            public, secrets, revision = self._values(profile_id)
        return {
            "config": public,
            "revision": revision,
            "secretStatus": {
                "svnPassword": bool(secrets.get("svn_credentials", {}).get("password")),
                "serverPassword": bool(secrets.get("server", {}).get("password")),
            },
        }

    def get_execution_config(self, profile_id: str) -> Dict[str, Any]:
        with self._lock:
            public, secrets, _ = self._values(profile_id)
            return merge_secrets(public, secrets)

    def save(self, profile_id: str, config: Dict[str, Any], revision: str) -> Dict[str, Any]:
        if not isinstance(config, dict):
            raise ValueError("profile config must be an object")
        with self._lock, self._db:
            current_public, current_secrets, current_revision = self._values(profile_id)
            if revision != current_revision:
                raise ProfileConflict("Personal configuration changed in this browser")
            public, secrets = split_secrets(config)
            incoming_user = (config.get("svn_credentials") or {}).get("username", "")
            incoming_user = incoming_user.strip() if isinstance(incoming_user, str) else ""
            incoming_password = (config.get("svn_credentials") or {}).get("password")
            old_password = (current_secrets.get("svn_credentials") or {}).get("password")

            if not incoming_user:
                public.pop("svn_credentials", None)
                secrets.pop("svn_credentials", None)
            elif incoming_password in (None, SECRET_MARKER) and old_password:
                public.setdefault("svn_credentials", {})["password"] = SECRET_MARKER
                secrets.setdefault("svn_credentials", {})["password"] = old_password
            elif incoming_password == "":
                if "svn_credentials" in public:
                    public["svn_credentials"]["password"] = ""
                if "svn_credentials" in secrets:
                    secrets["svn_credentials"]["password"] = ""

            incoming_server_user = (config.get("server") or {}).get("username", "")
            incoming_server_user = incoming_server_user.strip() if isinstance(incoming_server_user, str) else ""
            incoming_server_host = (config.get("server") or {}).get("host", "")
            incoming_server_host = incoming_server_host.strip() if isinstance(incoming_server_host, str) else ""
            incoming_server_pass = (config.get("server") or {}).get("password")
            old_server_pass = (current_secrets.get("server") or {}).get("password")

            if not incoming_server_user and not incoming_server_host:
                public.pop("server", None)
                secrets.pop("server", None)
            elif incoming_server_pass in (None, SECRET_MARKER) and old_server_pass:
                public.setdefault("server", {})["password"] = SECRET_MARKER
                secrets.setdefault("server", {})["password"] = old_server_pass
            elif incoming_server_pass == "":
                if "server" in public:
                    public["server"]["password"] = ""
                if "server" in secrets:
                    secrets["server"]["password"] = ""
            ciphertext = encrypt_secret_json(self.codec, secrets)
            self._db.execute(
                """INSERT INTO profiles(profile_id, config_json, secret_ciphertext, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(profile_id) DO UPDATE SET
                     config_json=excluded.config_json, secret_ciphertext=excluded.secret_ciphertext,
                     updated_at=CURRENT_TIMESTAMP""",
                (profile_id, json.dumps(public, ensure_ascii=False), ciphertext),
            )
        return self.get_public(profile_id)

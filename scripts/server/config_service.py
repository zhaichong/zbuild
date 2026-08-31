# -*- coding: utf-8 -*-
"""Optimistic, encrypted Web configuration persistence."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from server.secrets import DpapiSecretCodec, SecretCodec

_ENVELOPE_KEY = "$zbuildSecret"


def _is_secret_key(key: object) -> bool:
    value = str(key).replace("-", "_").lower()
    return (
        value in {"password", "secret", "token", "api_key", "apikey", "private_key", "privatekey"}
        or value.endswith("password")
        or value.endswith("token")
    )


class ConfigConflict(RuntimeError):
    pass


class WebConfigService:
    def __init__(self, path: Path, codec: Optional[SecretCodec] = None):
        self.path = Path(path).resolve()
        self.codec = codec or DpapiSecretCodec()

    def _read_raw(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Web config must contain a JSON object")
        return value

    def _revision(self) -> str:
        if not self.path.exists():
            return "0"
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def _public_copy(self, value: Any, path: Tuple[str, ...] = ()) -> Tuple[Any, Set[str]]:
        # 不再脱敏，直接返回真实值
        return value, set()

    def get_public(self) -> Dict[str, Any]:
        raw = self._read_raw()
        return {
            "config": self.get_execution_config(),
            "revision": self._revision(),
            "secretStatus": {
                "svnPassword": bool(raw.get("svn_credentials", {}).get("password")),
                "serverPassword": bool(raw.get("server", {}).get("password")),
            },
        }

    def _protect(
        self, incoming: Any, current: Any, clear_paths: Set[str], path: Tuple[str, ...] = ()
    ) -> Any:
        # 直接保存明文配置，保留未覆盖字段，无需占位符或加密封装
        if isinstance(incoming, dict):
            output = dict(incoming)
            current_dict = current if isinstance(current, dict) else {}
            for key, item in current_dict.items():
                if key not in output:
                    output[key] = item
            return output
        if isinstance(incoming, list):
            return list(incoming)
        return incoming

    def save(
        self, config: Dict[str, Any], revision: str, clear_secrets: Optional[Iterable[str]] = None
    ) -> Dict[str, Any]:
        if revision != self._revision():
            raise ConfigConflict("Configuration changed in another browser")
        if not isinstance(config, dict):
            raise ValueError("config must be an object")
        protected = self._protect(
            config, self._read_raw(), set(clear_secrets or ()), ()
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(protected, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_path.replace(self.path)
        return self.get_public()

    def _decrypt(self, value: Any) -> Any:
        if isinstance(value, dict):
            if set(value) == {_ENVELOPE_KEY}:
                return self.codec.decrypt(str(value[_ENVELOPE_KEY]))
            return {key: self._decrypt(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._decrypt(item) for item in value]
        return value

    def get_execution_config(self) -> Dict[str, Any]:
        return self._decrypt(self._read_raw())

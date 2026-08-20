# -*- coding: utf-8 -*-
"""Split secrets from persisted payloads and protect them with Windows DPAPI."""

import base64
import ctypes
import json
import os
from ctypes import wintypes
from typing import Any, Dict, Optional, Tuple

SECRET_MARKER = "[configured]"
_SECRET_NAMES = {
    "password", "secret", "token", "apikey", "api_key", "access_token",
    "refresh_token", "privatekey", "private_key",
}


def _is_secret_key(key: object) -> bool:
    normalized = str(key).replace("-", "_").lower()
    return normalized in _SECRET_NAMES or normalized.endswith("password") or normalized.endswith("token")


def split_secrets(value: Any) -> Tuple[Any, Any]:
    """Return a public copy and a sparse mirror containing secret values."""
    if isinstance(value, dict):
        public: Dict[str, Any] = {}
        secrets: Dict[str, Any] = {}
        for key, item in value.items():
            if _is_secret_key(key) and item not in (None, ""):
                public[key] = SECRET_MARKER
                secrets[key] = item
            else:
                public_item, secret_item = split_secrets(item)
                public[key] = public_item
                if secret_item not in (None, {}, []):
                    secrets[key] = secret_item
        return public, secrets
    if isinstance(value, list):
        public_list = []
        secret_map: Dict[str, Any] = {}
        for index, item in enumerate(value):
            public_item, secret_item = split_secrets(item)
            public_list.append(public_item)
            if secret_item not in (None, {}, []):
                secret_map[str(index)] = secret_item
        return public_list, secret_map
    return value, None


def merge_secrets(public: Any, secrets: Any) -> Any:
    """Merge a sparse secret mirror into its public payload copy."""
    if isinstance(public, dict):
        secret_dict = secrets if isinstance(secrets, dict) else {}
        return {
            key: merge_secrets(item, secret_dict.get(key))
            for key, item in public.items()
        }
    if isinstance(public, list):
        secret_dict = secrets if isinstance(secrets, dict) else {}
        return [merge_secrets(item, secret_dict.get(str(index))) for index, item in enumerate(public)]
    return secrets if secrets is not None else public


class SecretCodec:
    """Small injectable interface used by the task/config stores."""

    def encrypt(self, plaintext: str) -> str:
        raise NotImplementedError

    def decrypt(self, ciphertext: str) -> str:
        raise NotImplementedError


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


class DpapiSecretCodec(SecretCodec):
    PREFIX = "zbuild-dpapi:v1:"

    @staticmethod
    def _blob(data: bytes):
        buffer = ctypes.create_string_buffer(data)
        return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer

    def _crypt(self, data: bytes, decrypt: bool) -> bytes:
        if os.name != "nt":
            raise RuntimeError("Windows DPAPI is required to persist Web task secrets")
        in_blob, keepalive = self._blob(data)
        out_blob = _DataBlob()
        crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptProtectData.restype = wintypes.BOOL
        crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptUnprotectData.restype = wintypes.BOOL
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        if decrypt:
            ok = crypt32.CryptUnprotectData(
                ctypes.byref(in_blob), None, None, None, None, 1, ctypes.byref(out_blob)
            )
        else:
            ok = crypt32.CryptProtectData(
                ctypes.byref(in_blob), "zbuild", None, None, None, 1, ctypes.byref(out_blob)
            )
        del keepalive
        if not ok:
            raise OSError(ctypes.get_last_error(), "DPAPI operation failed")
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            kernel32.LocalFree(out_blob.pbData)

    def encrypt(self, plaintext: str) -> str:
        protected = self._crypt(plaintext.encode("utf-8"), decrypt=False)
        return self.PREFIX + base64.b64encode(protected).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext.startswith(self.PREFIX):
            raise ValueError("Unsupported secret ciphertext")
        raw = base64.b64decode(ciphertext[len(self.PREFIX):], validate=True)
        return self._crypt(raw, decrypt=True).decode("utf-8")


def encrypt_secret_json(codec: SecretCodec, secrets: Any) -> str:
    if secrets in (None, {}, []):
        return ""
    return codec.encrypt(json.dumps(secrets, ensure_ascii=False, separators=(",", ":")))


def decrypt_secret_json(codec: SecretCodec, ciphertext: str) -> Any:
    return json.loads(codec.decrypt(ciphertext)) if ciphertext else {}

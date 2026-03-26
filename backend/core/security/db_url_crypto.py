from __future__ import annotations

import base64
import hashlib
import os
import socket
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import TEXT, TypeDecorator

from config import settings


_ENCRYPTED_PREFIX = "enc:"
_KEY_DERIVATION_SALT = b"coze2dify-db-url-encryption"


def is_database_url_encrypted(value: str | None) -> bool:
    candidate = (value or "").strip()
    return candidate.startswith(_ENCRYPTED_PREFIX)


def encrypt_database_url(value: str | None) -> str | None:
    if value is None:
        return None

    plaintext = value.strip()
    if not plaintext:
        return ""
    if is_database_url_encrypted(plaintext):
        return plaintext

    token = _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{_ENCRYPTED_PREFIX}{token}"


def decrypt_database_url(value: str | None) -> str | None:
    if value is None:
        return None

    stored = value.strip()
    if not stored:
        return ""
    if not is_database_url_encrypted(stored):
        return stored

    token = stored[len(_ENCRYPTED_PREFIX) :]
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # noqa: BLE001 - surface actionable config error upstream
        raise RuntimeError(
            "Unable to decrypt persisted sync DB URLs. Check COZE2DIFY_DB_URL_ENCRYPTION_KEY."
        ) from exc


class EncryptedDatabaseUrl(TypeDecorator[str]):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect):  # type: ignore[override]
        del dialect
        return encrypt_database_url(value)

    def process_result_value(self, value: str | None, dialect):  # type: ignore[override]
        del dialect
        return decrypt_database_url(value)


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key(_resolve_key_material()))


def _derive_fernet_key(key_material: str) -> bytes:
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        key_material.encode("utf-8"),
        _KEY_DERIVATION_SALT,
        390_000,
        dklen=32,
    )
    return base64.urlsafe_b64encode(derived)


def _resolve_key_material() -> str:
    explicit_key = os.getenv("COZE2DIFY_DB_URL_ENCRYPTION_KEY", settings.db_url_encryption_key).strip()
    if explicit_key:
        return explicit_key

    if settings.debug or settings.database_url.startswith("sqlite"):
        return f"{settings.app_name}|{settings.database_url}|{socket.gethostname()}|dev-db-url-encryption"

    raise RuntimeError(
        "COZE2DIFY_DB_URL_ENCRYPTION_KEY must be set when persisting sync DB URLs outside local debug/sqlite environments."
    )

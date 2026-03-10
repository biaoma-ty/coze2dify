from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlsplit


_DB_URL_RE = re.compile(
    r"(?P<url>(?:postgres(?:ql)?|mysql|mariadb|sqlite|oracle|mssql(?:\+pyodbc)?):\/\/[^\s'\"<>]+)",
    re.IGNORECASE,
)


def build_database_ref(db_url: str | None) -> dict[str, str | int | None] | None:
    if not db_url:
        return None

    value = str(db_url).strip()
    if not value:
        return None

    parts = urlsplit(value)
    scheme = parts.scheme or None
    host = parts.hostname or None
    port = parts.port
    database = parts.path.lstrip("/") or None

    if scheme == "sqlite":
        database = database or parts.netloc or None
        display_url = "sqlite:///***"
        if database:
            display_url = f"sqlite:///***/{database.split('/')[-1]}"
        return {
            "scheme": scheme,
            "host": None,
            "port": None,
            "database": database,
            "display_url": display_url,
        }

    location = host or parts.netloc.rsplit("@", 1)[-1] or "***"
    if host and port:
        location = f"{host}:{port}"

    display_url = value
    if scheme:
        display_url = f"{scheme}://***@{location}"
    elif location:
        display_url = f"***@{location}"

    if database:
        display_url = f"{display_url}/{database}"

    return {
        "scheme": scheme,
        "host": host or None,
        "port": port,
        "database": database,
        "display_url": display_url,
    }


def redact_database_url(db_url: str | None) -> str | None:
    ref = build_database_ref(db_url)
    if ref is None:
        return None
    return str(ref["display_url"])


def sanitize_error_message(
    message: str,
    *,
    db_urls: Iterable[str] = (),
    secrets: Iterable[str] = (),
) -> str:
    sanitized = message

    for secret in secrets:
        value = (secret or "").strip()
        if value:
            sanitized = sanitized.replace(value, "[REDACTED]")

    for db_url in db_urls:
        value = (db_url or "").strip()
        if not value:
            continue
        sanitized = sanitized.replace(value, redact_database_url(value) or "[REDACTED]")

    return _DB_URL_RE.sub(lambda match: redact_database_url(match.group("url")) or "[REDACTED]", sanitized)


def sanitize_exception(
    exc: Exception,
    *,
    db_urls: Iterable[str] = (),
    secrets: Iterable[str] = (),
) -> str:
    return sanitize_error_message(str(exc), db_urls=db_urls, secrets=secrets)

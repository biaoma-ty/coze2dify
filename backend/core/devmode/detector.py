"""
Auto-detect locally deployed Coze Studio / Dify instances by scanning
docker-compose files and .env files for database connection info.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DetectedService:
    """Represents a detected local deployment."""

    name: str  # "dify" | "coze-studio"
    path: str  # directory where docker-compose was found
    db_url: str = ""  # constructed PostgreSQL URL
    api_url: str = ""  # e.g. http://localhost:80
    docker_compose_found: bool = False
    env_file_found: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class DevModeDetector:
    """Scans filesystem for local Coze Studio / Dify deployments."""

    def __init__(
        self,
        dify_paths: list[str] | None = None,
        coze_paths: list[str] | None = None,
    ) -> None:
        from config import settings

        self.dify_paths = dify_paths or settings.dev_mode_dify_paths
        self.coze_paths = coze_paths or settings.dev_mode_coze_paths

    # ── public ───────────────────────────────────────────────

    def detect_all(self) -> dict[str, list[DetectedService]]:
        """Return all detected local deployments grouped by platform."""
        return {
            "dify": self._scan_paths(self.dify_paths, self._detect_dify),
            "coze": self._scan_paths(self.coze_paths, self._detect_coze),
        }

    # ── internal ─────────────────────────────────────────────

    @staticmethod
    def _scan_paths(
        paths: list[str],
        detector,
    ) -> list[DetectedService]:
        results: list[DetectedService] = []
        seen: set[str] = set()
        for raw_path in paths:
            expanded = os.path.expanduser(raw_path)
            resolved = str(Path(expanded).resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            if not os.path.isdir(resolved):
                continue
            svc = detector(resolved)
            if svc is not None:
                results.append(svc)
        return results

    # ── Dify ─────────────────────────────────────────────────

    @staticmethod
    def _detect_dify(path: str) -> DetectedService | None:
        """Look for Dify's docker-compose.yaml and extract DB config."""
        compose_candidates = [
            os.path.join(path, "docker-compose.yaml"),
            os.path.join(path, "docker-compose.yml"),
        ]
        compose_path = None
        for c in compose_candidates:
            if os.path.isfile(c):
                compose_path = c
                break
        if compose_path is None:
            return None

        svc = DetectedService(
            name="dify",
            path=path,
            docker_compose_found=True,
        )

        # Try to read .env in same directory
        env_path = os.path.join(path, ".env")
        env_vars: dict[str, str] = {}
        if os.path.isfile(env_path):
            svc.env_file_found = True
            env_vars = DevModeDetector._parse_env_file(env_path)

        # Extract DB connection from .env (Dify convention)
        db_user = env_vars.get("DB_USERNAME", env_vars.get("POSTGRES_USER", "postgres"))
        db_pass = env_vars.get("DB_PASSWORD", env_vars.get("POSTGRES_PASSWORD", "difyai123456"))
        db_host = env_vars.get("DB_HOST", "localhost")
        db_port = env_vars.get("DB_PORT", "5432")
        db_name = env_vars.get("DB_DATABASE", env_vars.get("POSTGRES_DB", "dify"))

        svc.db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        # Dify default web port
        nginx_port = env_vars.get("NGINX_PORT", env_vars.get("EXPOSE_NGINX_PORT", "80"))
        svc.api_url = f"http://localhost:{nginx_port}"

        svc.extra = {
            "db_user": db_user,
            "db_host": db_host,
            "db_port": db_port,
            "db_name": db_name,
        }

        return svc

    # ── Coze Studio ──────────────────────────────────────────

    @staticmethod
    def _detect_coze(path: str) -> DetectedService | None:
        """Look for Coze Studio docker-compose and extract config."""
        compose_candidates = [
            os.path.join(path, "docker-compose.yaml"),
            os.path.join(path, "docker-compose.yml"),
        ]
        compose_path = None
        for c in compose_candidates:
            if os.path.isfile(c):
                compose_path = c
                break
        if compose_path is None:
            return None

        svc = DetectedService(
            name="coze-studio",
            path=path,
            docker_compose_found=True,
        )

        env_path = os.path.join(path, ".env")
        env_vars: dict[str, str] = {}
        if os.path.isfile(env_path):
            svc.env_file_found = True
            env_vars = DevModeDetector._parse_env_file(env_path)

        # Coze Studio typically uses PostgreSQL too
        db_user = env_vars.get("POSTGRES_USER", env_vars.get("DB_USER", "postgres"))
        db_pass = env_vars.get("POSTGRES_PASSWORD", env_vars.get("DB_PASSWORD", ""))
        db_host = env_vars.get("DB_HOST", "localhost")
        db_port = env_vars.get("DB_PORT", "5432")
        db_name = env_vars.get("POSTGRES_DB", env_vars.get("DB_NAME", "coze"))

        if db_pass:
            svc.db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        else:
            svc.db_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"

        api_port = env_vars.get("API_PORT", env_vars.get("PORT", "8788"))
        svc.api_url = f"http://localhost:{api_port}"

        return svc

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    def _parse_env_file(path: str) -> dict[str, str]:
        """Parse a .env file into a dict, skipping comments and blank lines."""
        result: dict[str, str] = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
                    if m:
                        key = m.group(1)
                        value = m.group(2).strip().strip("'\"")
                        result[key] = value
        except OSError:
            pass
        return result

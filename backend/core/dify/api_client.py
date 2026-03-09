"""Client for interacting with Dify Console / API."""

from __future__ import annotations

from typing import Any

import httpx

from config import settings


class DifyApiClient:
    """Client for fetching app / workflow data from a Dify instance."""

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.api_base = (api_base or settings.dify_api_base).rstrip("/")
        self.api_key = api_key or settings.dify_api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ── connection test ──────────────────────────────────────

    async def test_connection(self) -> dict[str, Any]:
        """Verify that the Dify API is reachable and the token is valid."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try console API first (for self-hosted / admin tokens)
                resp = await client.get(
                    f"{self.api_base}/console/api/apps",
                    headers=self._headers(),
                    params={"page": 1, "limit": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    total = data.get("total", data.get("data", []))
                    return {
                        "connected": True,
                        "mode": "console",
                        "total": total if isinstance(total, int) else len(total),
                    }

                # Fallback: try service API (some tokens only have service-level access)
                resp2 = await client.get(
                    f"{self.api_base}/v1/parameters",
                    headers=self._headers(),
                )
                if resp2.status_code == 200:
                    return {"connected": True, "mode": "service", "total": -1}

                return {
                    "connected": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    # ── list apps ────────────────────────────────────────────

    async def list_apps(self, page: int = 1, limit: int = 100) -> list[dict[str, Any]]:
        """List Dify apps via the console API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_base}/console/api/apps",
                headers=self._headers(),
                params={"page": page, "limit": limit},
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", data.get("items", []))
            return [
                {
                    "app_id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "mode": item.get("mode", ""),
                    "description": item.get("description", ""),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                }
                for item in items
            ]

    # ── get single app detail ────────────────────────────────

    async def get_app_detail(self, app_id: str) -> dict[str, Any]:
        """Fetch detailed info for one Dify app."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_base}/console/api/apps/{app_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

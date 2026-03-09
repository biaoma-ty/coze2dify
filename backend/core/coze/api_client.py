from __future__ import annotations

from typing import Any

import httpx

from config import settings


class CozeApiClient:
    """Client for fetching workflows from Coze API."""

    def __init__(self, access_token: str | None = None, base_url: str | None = None) -> None:
        self.access_token = access_token or settings.coze_access_token
        self.base_url = (base_url or settings.coze_api_base).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # ── connection test ──────────────────────────────────────

    async def test_connection(self) -> dict[str, Any]:
        """Verify the PAT token is valid by fetching workspace list."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/workspaces",
                    headers=self._headers(),
                    params={"page_size": 1, "page_num": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    workspaces = data.get("data", {}).get("workspaces", [])
                    total = data.get("data", {}).get("total_count", len(workspaces))
                    return {
                        "connected": True,
                        "workspaces": total,
                    }
                return {
                    "connected": False,
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    # ── workspaces ───────────────────────────────────────────

    async def list_spaces(self) -> list[dict[str, Any]]:
        """List accessible workspaces / spaces."""
        async with httpx.AsyncClient(timeout=30) as client:
            all_spaces: list[dict[str, Any]] = []
            page = 1
            while True:
                resp = await client.get(
                    f"{self.base_url}/v1/workspaces",
                    headers=self._headers(),
                    params={"page_size": 50, "page_num": page},
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                items = data.get("workspaces", [])
                for ws in items:
                    all_spaces.append(
                        {
                            "id": ws.get("id", ""),
                            "name": ws.get("name", ""),
                        }
                    )
                total = data.get("total_count", 0)
                if len(all_spaces) >= total or not items:
                    break
                page += 1
            return all_spaces

    # ── bots / published bots in a space ─────────────────────

    async def list_bots(self, space_id: str) -> list[dict[str, Any]]:
        """List published bots in a workspace/space."""
        async with httpx.AsyncClient(timeout=30) as client:
            all_bots: list[dict[str, Any]] = []
            page = 1
            while True:
                resp = await client.get(
                    f"{self.base_url}/v1/space/published_bots_list",
                    headers=self._headers(),
                    params={
                        "space_id": space_id,
                        "page_size": 50,
                        "page_index": page,
                    },
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                items = data.get("space_bots", data.get("bots", []))
                for bot in items:
                    all_bots.append(
                        {
                            "bot_id": bot.get("bot_id", ""),
                            "bot_name": bot.get("bot_name", ""),
                            "description": bot.get("description", ""),
                            "publish_time": bot.get("publish_time", ""),
                        }
                    )
                total = data.get("total", 0)
                if len(all_bots) >= total or not items:
                    break
                page += 1
            return all_bots

    # ── workflows ────────────────────────────────────────────

    async def list_workflows(self, space_id: str) -> list[dict[str, Any]]:
        """List workflows in a workspace by iterating bots and filtering."""
        bots = await self.list_bots(space_id)
        # Coze API doesn't have a direct "list workflows" endpoint.
        # Each bot may contain workflow info. Return bots as selectable items.
        return bots

    async def fetch_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Fetch a single workflow by ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/v1/workflows/{workflow_id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

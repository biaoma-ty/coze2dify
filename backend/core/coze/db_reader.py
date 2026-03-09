from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text


class CozeDbReader:
    """Reads workflow data directly from Coze database."""

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, pool_pre_ping=True)

    def list_workflows(self) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                        SELECT wm.id,
                               wm.name,
                               COALESCE(wm.description, '') AS description,
                               COALESCE(wm.updated_at, wm.created_at) AS updated_at,
                               CASE WHEN wd.canvas IS NULL OR wd.deleted_at IS NOT NULL THEN 0 ELSE 1 END AS has_draft
                        FROM workflow_meta wm
                        LEFT JOIN workflow_draft wd ON wd.id = wm.id
                        WHERE wm.deleted_at IS NULL
                        ORDER BY COALESCE(wm.updated_at, wm.created_at) DESC
                        """
                    )
                )
                return [
                    {
                        "id": str(row[0]),
                        "name": row[1] or "",
                        "description": row[2] or "",
                        "updated_at": str(row[3]) if row[3] is not None else "",
                        "has_draft": bool(row[4]),
                    }
                    for row in result
                ]
            except Exception:
                result = conn.execute(text("SELECT id, name, canvas FROM workflows"))
                return [
                    {
                        "id": str(row[0]),
                        "name": row[1] or "",
                        "description": "",
                        "updated_at": "",
                        "has_draft": bool(row[2]),
                    }
                    for row in result
                ]

    def read_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                        SELECT wd.canvas,
                               wm.name,
                               COALESCE(wm.description, '') AS description
                        FROM workflow_draft wd
                        LEFT JOIN workflow_meta wm ON wm.id = wd.id
                        WHERE wd.id = :id AND wd.deleted_at IS NULL
                        """
                    ),
                    {"id": workflow_id},
                )
                row = result.fetchone()
                if row is None:
                    return None

                canvas = self._decode_json(row[0])
                if canvas is None:
                    return None

                return {
                    "id": str(workflow_id),
                    "name": row[1] or "",
                    "description": row[2] or "",
                    "canvas": canvas,
                }
            except Exception:
                result = conn.execute(text("SELECT canvas FROM workflows WHERE id = :id"), {"id": workflow_id})
                row = result.fetchone()
                if row is None:
                    return None
                canvas = self._decode_json(row[0])
                return {"id": str(workflow_id), "name": "", "description": "", "canvas": canvas} if canvas else None

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def _decode_json(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                return None
            return decoded if isinstance(decoded, dict) else None
        return None

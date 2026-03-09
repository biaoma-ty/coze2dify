"""Read workflow data directly from Dify's PostgreSQL database."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text


class DifyDbReader:
    """Reads app / workflow data from a Dify PostgreSQL instance."""

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def list_apps(self) -> list[dict[str, Any]]:
        """List all workflow-type apps from Dify's apps table."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT a.id, a.name, a.mode, a.description,
                           a.created_at, a.updated_at,
                           w.id AS workflow_id
                    FROM apps a
                    LEFT JOIN workflows w ON w.app_id = a.id
                    WHERE a.mode IN ('workflow', 'advanced-chat')
                    ORDER BY a.updated_at DESC
                """)
            )
            return [
                {
                    "app_id": str(row[0]),
                    "name": row[1],
                    "mode": row[2],
                    "description": row[3] or "",
                    "created_at": str(row[4]) if row[4] else "",
                    "updated_at": str(row[5]) if row[5] else "",
                    "workflow_id": str(row[6]) if row[6] else "",
                }
                for row in result
            ]

    def read_workflow(self, app_id: str) -> dict[str, Any] | None:
        """Read the workflow graph JSON for a given app ID."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT graph, features FROM workflows WHERE app_id = :app_id"),
                {"app_id": app_id},
            )
            row = result.fetchone()
            if row is None:
                return None

            graph = row[0]
            features = row[1]
            # graph may be stored as JSON string or native JSONB
            if isinstance(graph, str):
                graph = json.loads(graph)
            if isinstance(features, str):
                features = json.loads(features)
            return {
                "app_id": app_id,
                "graph": graph,
                "features": features,
            }

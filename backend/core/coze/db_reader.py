from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, text


class CozeDbReader:
    """Reads workflow data directly from Coze database."""

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)

    def list_workflows(self) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            # TODO: Adapt to actual Coze DB schema
            result = conn.execute(text("SELECT id, name, canvas FROM workflows"))
            return [{"id": row[0], "name": row[1], "canvas": row[2]} for row in result]

    def read_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT canvas FROM workflows WHERE id = :id"), {"id": workflow_id})
            row = result.fetchone()
            return row[0] if row else None

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

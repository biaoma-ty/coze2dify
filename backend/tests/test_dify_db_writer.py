from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, text

from core.dify.db_writer import DifyDbWriter
from core.dify.models import DifyDSL


def _setup_minimal_dify_tables(db_url: str) -> None:
    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE apps (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        description TEXT,
                        icon TEXT,
                        icon_background TEXT,
                        icon_type TEXT,
                        updated_by TEXT,
                        updated_at TEXT
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE workflows (
                        app_id TEXT PRIMARY KEY,
                        graph TEXT NOT NULL,
                        features TEXT NOT NULL,
                        environment_variables TEXT NOT NULL,
                        conversation_variables TEXT NOT NULL,
                        rag_pipeline_variables TEXT NOT NULL,
                        updated_by TEXT,
                        updated_at TEXT
                    )
                    """
                )
            )
    finally:
        engine.dispose()


def test_update_workflow_updates_app_metadata_and_graph(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'dify-update-success.db'}"
    _setup_minimal_dify_tables(db_url)
    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO apps (id, name, mode, description, icon, icon_background, icon_type, updated_by, updated_at)
                    VALUES ('app-1', 'Old Name', 'workflow', 'old', '', '', NULL, 'seed', '2026-01-01T00:00:00')
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO workflows (app_id, graph, features, environment_variables, conversation_variables, rag_pipeline_variables, updated_by, updated_at)
                    VALUES ('app-1', '{}', '{}', '{}', '{}', '{}', 'seed', '2026-01-01T00:00:00')
                    """
                )
            )
    finally:
        engine.dispose()

    writer = DifyDbWriter(db_url)
    writer._ensure_owner_context = lambda conn: ("tenant", "account")  # type: ignore[method-assign]

    dsl = DifyDSL.model_validate(
        {
            "app": {
                "mode": "advanced-chat",
                "name": "New Name",
                "description": "new description",
                "icon": "🤖",
                "icon_background": "#FFEAD5",
            },
            "workflow": {
                "graph": {"nodes": [{"id": "n1", "data": {"type": "start"}}], "edges": []},
                "features": {"flag": True},
            },
        }
    )

    writer.update_workflow("app-1", dsl)

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            app_row = conn.execute(
                text("SELECT name, mode, description, icon, icon_background, icon_type FROM apps WHERE id = 'app-1'")
            ).fetchone()
            workflow_row = conn.execute(text("SELECT graph, features FROM workflows WHERE app_id = 'app-1'")).fetchone()
    finally:
        engine.dispose()

    assert app_row == ("New Name", "advanced-chat", "new description", "🤖", "#FFEAD5", "emoji")
    assert json.loads(workflow_row[0])["nodes"][0]["id"] == "n1"
    assert json.loads(workflow_row[1]) == {"flag": True}


def test_update_workflow_raises_when_app_is_missing(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'dify-update-missing.db'}"
    _setup_minimal_dify_tables(db_url)
    writer = DifyDbWriter(db_url)
    writer._ensure_owner_context = lambda conn: ("tenant", "account")  # type: ignore[method-assign]

    with pytest.raises(LookupError, match="missing-app"):
        writer.update_workflow("missing-app", DifyDSL())

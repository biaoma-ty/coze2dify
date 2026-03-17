from __future__ import annotations

import json

from sqlalchemy import create_engine, text

from core.dify.db_reader import DifyDbReader


def test_read_workflow_includes_state_variable_artifacts(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'dify-reader.db'}"
    engine = create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE workflows (
                        app_id TEXT PRIMARY KEY,
                        graph TEXT NOT NULL,
                        features TEXT NOT NULL,
                        environment_variables TEXT NOT NULL,
                        conversation_variables TEXT NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO workflows (
                        app_id, graph, features, environment_variables, conversation_variables
                    )
                    VALUES (
                        'app-1',
                        :graph,
                        :features,
                        :environment_variables,
                        :conversation_variables
                    )
                    """
                ),
                {
                    "graph": json.dumps({"nodes": [{"id": "n1"}], "edges": []}),
                    "features": json.dumps({"feature": True}),
                    "environment_variables": json.dumps(
                        {
                            "api_key": {
                                "name": "api_key",
                                "value_type": "string",
                                "value": "secret",
                                "description": "API key",
                            }
                        }
                    ),
                    "conversation_variables": json.dumps(
                        {
                            "memory": {
                                "name": "memory",
                                "value_type": "string",
                                "value": "",
                                "description": "Conversation memory",
                                "selector": ["conversation", "memory"],
                            }
                        }
                    ),
                },
            )
    finally:
        engine.dispose()

    workflow = DifyDbReader(db_url).read_workflow("app-1")

    assert workflow is not None
    assert workflow["graph"]["nodes"][0]["id"] == "n1"
    assert workflow["environment_variables"] == {
        "api_key": {
            "name": "api_key",
            "value_type": "string",
            "value": "secret",
            "description": "API key",
        }
    }
    assert workflow["conversation_variables"] == {
        "memory": {
            "name": "memory",
            "value_type": "string",
            "value": "",
            "description": "Conversation memory",
            "selector": ["conversation", "memory"],
        }
    }

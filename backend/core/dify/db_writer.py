from __future__ import annotations

import json
from datetime import UTC, datetime
import uuid
from typing import Any

from sqlalchemy import create_engine, text

from .models import DifyDSL


class DifyDbWriter:
    """Writes workflow data directly to Dify PostgreSQL database."""

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url)

    def write_workflow(self, dsl: DifyDSL) -> str:
        app_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        app_config = dsl.app
        now = datetime.now(UTC).replace(tzinfo=None)

        with self.engine.begin() as conn:
            tenant_id, account_id = self._ensure_owner_context(conn)
            self._ensure_setup_marker(conn)

            # Create app
            conn.execute(
                text("""
                    INSERT INTO apps (
                        id, tenant_id, name, mode, description, icon, icon_background,
                        icon_type, workflow_id, enable_site, enable_api,
                        api_rpm, api_rph, is_demo, is_public, is_universal,
                        created_by, updated_by, created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant_id, :name, :mode, :desc, :icon, :icon_bg,
                        :icon_type, :workflow_id, :enable_site, :enable_api,
                        :api_rpm, :api_rph, :is_demo, :is_public, :is_universal,
                        :created_by, :updated_by, :created_at, :updated_at
                    )
                """),
                {
                    "id": app_id,
                    "tenant_id": tenant_id,
                    "name": app_config.get("name", ""),
                    "mode": app_config.get("mode", "workflow"),
                    "desc": app_config.get("description", ""),
                    "icon": app_config.get("icon", ""),
                    "icon_bg": app_config.get("icon_background", ""),
                    "icon_type": "emoji" if app_config.get("icon") else None,
                    "workflow_id": workflow_id,
                    "enable_site": False,
                    "enable_api": False,
                    "api_rpm": 0,
                    "api_rph": 0,
                    "is_demo": False,
                    "is_public": False,
                    "is_universal": False,
                    "created_by": account_id,
                    "updated_by": account_id,
                    "created_at": now,
                    "updated_at": now,
                },
            )

            # Create workflow
            graph_json = json.dumps(dsl.workflow.graph.model_dump())
            features_json = json.dumps(dsl.workflow.features or {})
            environment_variables_json = self._serialize_named_variables(dsl.workflow.environment_variables)
            conversation_variables_json = self._serialize_named_variables(dsl.workflow.conversation_variables)
            rag_pipeline_variables_json = self._serialize_named_variables([])
            workflow_type = "workflow" if app_config.get("mode", "workflow") == "workflow" else "chat"

            conn.execute(
                text("""
                    INSERT INTO workflows (
                        id, tenant_id, app_id, type, version, graph, features,
                        created_by, updated_by, created_at, updated_at,
                        environment_variables, conversation_variables, rag_pipeline_variables,
                        marked_name, marked_comment
                    )
                    VALUES (
                        :id, :tenant_id, :app_id, :type, :version, :graph, :features,
                        :created_by, :updated_by, :created_at, :updated_at,
                        :environment_variables, :conversation_variables, :rag_pipeline_variables,
                        :marked_name, :marked_comment
                    )
                """),
                {
                    "id": workflow_id,
                    "tenant_id": tenant_id,
                    "app_id": app_id,
                    "type": workflow_type,
                    "version": "draft",
                    "graph": graph_json,
                    "features": features_json,
                    "created_by": account_id,
                    "updated_by": account_id,
                    "created_at": now,
                    "updated_at": now,
                    "environment_variables": environment_variables_json,
                    "conversation_variables": conversation_variables_json,
                    "rag_pipeline_variables": rag_pipeline_variables_json,
                    "marked_name": "",
                    "marked_comment": "",
                },
            )

        return app_id

    def update_workflow(self, app_id: str, dsl: DifyDSL) -> None:
        graph_json = json.dumps(dsl.workflow.graph.model_dump())
        features_json = json.dumps(dsl.workflow.features or {})
        environment_variables_json = self._serialize_named_variables(dsl.workflow.environment_variables)
        conversation_variables_json = self._serialize_named_variables(dsl.workflow.conversation_variables)
        rag_pipeline_variables_json = self._serialize_named_variables([])
        now = datetime.now(UTC).replace(tzinfo=None)

        with self.engine.begin() as conn:
            _, account_id = self._ensure_owner_context(conn)
            conn.execute(
                text("""
                    UPDATE workflows
                    SET graph = :graph,
                        features = :features,
                        environment_variables = :environment_variables,
                        conversation_variables = :conversation_variables,
                        rag_pipeline_variables = :rag_pipeline_variables,
                        updated_by = :updated_by,
                        updated_at = :updated_at
                    WHERE app_id = :app_id
                """),
                {
                    "graph": graph_json,
                    "features": features_json,
                    "environment_variables": environment_variables_json,
                    "conversation_variables": conversation_variables_json,
                    "rag_pipeline_variables": rag_pipeline_variables_json,
                    "updated_by": account_id,
                    "updated_at": now,
                    "app_id": app_id,
                },
            )

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def _ensure_setup_marker(conn: Any) -> None:
        setup_exists = conn.execute(text("SELECT 1 FROM dify_setups LIMIT 1")).scalar()
        if setup_exists:
            return

        conn.execute(
            text("INSERT INTO dify_setups (version) VALUES (:version)"),
            {"version": "coze2dify-bootstrap"},
        )

    def _ensure_owner_context(self, conn: Any) -> tuple[str, str]:
        row = conn.execute(
            text("""
            SELECT tenant_id, account_id
            FROM tenant_account_joins
            WHERE role = 'owner'
            ORDER BY current DESC, created_at ASC
            LIMIT 1
        """)
        ).fetchone()
        if row:
            return str(row[0]), str(row[1])

        account_id = conn.execute(text("SELECT id FROM accounts ORDER BY created_at ASC LIMIT 1")).scalar()
        if account_id is None:
            account_id = str(uuid.uuid4())
            now = datetime.now(UTC).replace(tzinfo=None)
            conn.execute(
                text("""
                    INSERT INTO accounts (
                        id, name, email, status, initialized_at,
                        created_at, updated_at, last_active_at,
                        interface_language, interface_theme, timezone
                    )
                    VALUES (
                        :id, :name, :email, :status, :initialized_at,
                        :created_at, :updated_at, :last_active_at,
                        :interface_language, :interface_theme, :timezone
                    )
                """),
                {
                    "id": account_id,
                    "name": "coze2dify",
                    "email": f"coze2dify+{account_id[:8]}@local.invalid",
                    "status": "active",
                    "initialized_at": now,
                    "created_at": now,
                    "updated_at": now,
                    "last_active_at": now,
                    "interface_language": "en-US",
                    "interface_theme": "light",
                    "timezone": "UTC",
                },
            )

        tenant_id = conn.execute(text("SELECT id FROM tenants ORDER BY created_at ASC LIMIT 1")).scalar()
        if tenant_id is None:
            tenant_id = str(uuid.uuid4())
            now = datetime.now(UTC).replace(tzinfo=None)
            conn.execute(
                text("""
                    INSERT INTO tenants (id, name, plan, status, created_at, updated_at)
                    VALUES (:id, :name, :plan, :status, :created_at, :updated_at)
                """),
                {
                    "id": tenant_id,
                    "name": "coze2dify",
                    "plan": "basic",
                    "status": "normal",
                    "created_at": now,
                    "updated_at": now,
                },
            )

        join_exists = conn.execute(
            text("""
                SELECT 1
                FROM tenant_account_joins
                WHERE tenant_id = :tenant_id AND account_id = :account_id
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "account_id": account_id},
        ).scalar()
        if not join_exists:
            conn.execute(
                text("""
                    INSERT INTO tenant_account_joins (id, tenant_id, account_id, role, current)
                    VALUES (:id, :tenant_id, :account_id, :role, :current)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "role": "owner",
                    "current": True,
                },
            )

        return str(tenant_id), str(account_id)

    @staticmethod
    def _serialize_named_variables(variables: list[Any]) -> str:
        if not variables:
            return "{}"

        payload: dict[str, Any] = {}
        for index, variable in enumerate(variables):
            if not isinstance(variable, dict):
                continue
            key = str(variable.get("name") or variable.get("variable") or variable.get("id") or f"var_{index}")
            payload[key] = variable

        return json.dumps(payload, ensure_ascii=False)

from __future__ import annotations

import json
import os
import uuid
from urllib.parse import SplitResult, urlsplit, urlunsplit

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.dify.db_reader import DifyDbReader
from core.engine.conversion_service import ConversionService
from core.sync.sync_engine import SyncEngine
from db.database import Base
from db.models import SyncConfig, SyncHistory


POSTGRES_ADMIN_URL = os.getenv("COZE2DIFY_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_ADMIN_URL,
    reason="COZE2DIFY_TEST_POSTGRES_URL is required for PostgreSQL integration tests",
)


def _minimal_canvas(node_prefix: str) -> dict[str, object]:
    start_id = f"{node_prefix}-start"
    end_id = f"{node_prefix}-end"
    return {
        "nodes": [
            {
                "id": start_id,
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
            },
            {
                "id": end_id,
                "type": "2",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {"inputs": {"terminatePlan": "useAnswerContent"}},
            },
        ],
        "edges": [{"sourceNodeID": start_id, "targetNodeID": end_id}],
        "versions": {},
    }


def _replace_database(url: str, database: str) -> str:
    parts = urlsplit(url)
    replaced = SplitResult(
        scheme=parts.scheme,
        netloc=parts.netloc,
        path=f"/{database}",
        query=parts.query,
        fragment=parts.fragment,
    )
    return urlunsplit(replaced)


def _create_database(admin_url: str, database: str) -> str:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{database}"'))
    finally:
        engine.dispose()
    return _replace_database(admin_url, database)


def _drop_database(admin_url: str, database: str) -> None:
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
    finally:
        engine.dispose()


@pytest.fixture
def postgres_db_url() -> str:
    assert POSTGRES_ADMIN_URL is not None
    database = f"coze2dify_it_{uuid.uuid4().hex[:8]}"
    db_url = _create_database(POSTGRES_ADMIN_URL, database)
    try:
        yield db_url
    finally:
        _drop_database(POSTGRES_ADMIN_URL, database)


def _create_postgres_fixture_schema(db_url: str) -> None:
    engine = create_engine(db_url, pool_pre_ping=True)
    statements = [
        """
        CREATE TABLE workflow_meta (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NULL,
            deleted_at TIMESTAMP NULL
        )
        """,
        """
        CREATE TABLE workflow_draft (
            id TEXT PRIMARY KEY,
            canvas JSONB NOT NULL,
            deleted_at TIMESTAMP NULL
        )
        """,
        """
        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            initialized_at TIMESTAMP NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            last_active_at TIMESTAMP NULL,
            interface_language TEXT,
            interface_theme TEXT,
            timezone TEXT
        )
        """,
        """
        CREATE TABLE tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE tenant_account_joins (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            role TEXT NOT NULL,
            current BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE dify_setups (
            version TEXT PRIMARY KEY
        )
        """,
        """
        CREATE TABLE apps (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            mode TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            icon_background TEXT,
            icon_type TEXT,
            workflow_id TEXT,
            enable_site BOOLEAN NOT NULL,
            enable_api BOOLEAN NOT NULL,
            api_rpm INTEGER NOT NULL,
            api_rph INTEGER NOT NULL,
            is_demo BOOLEAN NOT NULL,
            is_public BOOLEAN NOT NULL,
            is_universal BOOLEAN NOT NULL,
            created_by TEXT,
            updated_by TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE workflows (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            app_id TEXT NOT NULL,
            type TEXT NOT NULL,
            version TEXT NOT NULL,
            graph JSONB NOT NULL,
            features JSONB NOT NULL,
            created_by TEXT,
            updated_by TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            environment_variables JSONB NOT NULL DEFAULT '{}'::jsonb,
            conversation_variables JSONB NOT NULL DEFAULT '{}'::jsonb,
            rag_pipeline_variables JSONB NOT NULL DEFAULT '{}'::jsonb,
            marked_name TEXT,
            marked_comment TEXT
        )
        """,
    ]

    try:
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
    finally:
        engine.dispose()


def _seed_coze_workflow(db_url: str, workflow_id: str, name: str, canvas: dict[str, object]) -> None:
    engine = create_engine(db_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO workflow_meta (id, name, description, created_at, updated_at, deleted_at)
                    VALUES (:id, :name, '', NOW(), NOW(), NULL)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = NOW(),
                        deleted_at = NULL
                    """
                ),
                {"id": workflow_id, "name": name},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO workflow_draft (id, canvas, deleted_at)
                    VALUES (:id, CAST(:canvas AS JSONB), NULL)
                    ON CONFLICT (id) DO UPDATE SET
                        canvas = CAST(:canvas AS JSONB),
                        deleted_at = NULL
                    """
                ),
                {"id": workflow_id, "canvas": json.dumps(canvas)},
            )
    finally:
        engine.dispose()


def _metadata_session_factory(sqlite_path: str):
    engine = create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_postgres_direct_write_create_and_update(postgres_db_url: str, tmp_path) -> None:
    _create_postgres_fixture_schema(postgres_db_url)
    session_factory = _metadata_session_factory(str(tmp_path / "metadata-direct.db"))
    service = ConversionService()
    reader = DifyDbReader(postgres_db_url)

    with session_factory() as db:
        first = service.convert_uploaded_file(
            db,
            json.dumps(_minimal_canvas("direct-a")).encode(),
            "direct-a.json",
        )
        created = service.write_to_dify(db, first["conversion_id"], db_url=postgres_db_url)
        app_id = str(created["app_id"])

        second = service.convert_uploaded_file(
            db,
            json.dumps(_minimal_canvas("direct-b")).encode(),
            "direct-b.json",
        )
        updated = service.write_to_dify(
            db,
            second["conversion_id"],
            db_url=postgres_db_url,
            app_id=app_id,
        )

    apps = reader.list_apps()
    workflow = reader.read_workflow(app_id)

    assert created["status"] == "written"
    assert created["mode"] == "create"
    assert updated["status"] == "updated"
    assert updated["mode"] == "update"
    assert len(apps) == 1
    assert apps[0]["app_id"] == app_id
    assert workflow is not None
    assert {node["id"] for node in workflow["graph"]["nodes"]} == {"direct-b-start", "direct-b-end"}


def test_postgres_sync_execution_create_and_update(postgres_db_url: str, tmp_path) -> None:
    _create_postgres_fixture_schema(postgres_db_url)
    _seed_coze_workflow(postgres_db_url, "wf-sync", "Sync Flow", _minimal_canvas("sync-a"))
    session_factory = _metadata_session_factory(str(tmp_path / "metadata-sync.db"))
    sync_engine = SyncEngine()
    reader = DifyDbReader(postgres_db_url)

    with session_factory() as db:
        config = SyncConfig(
            name="Postgres Sync",
            coze_db_url=postgres_db_url,
            dify_db_url=postgres_db_url,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        first = sync_engine.execute_sync(db, config)
        app_id = first["items"][0]["target_app_id"]

        _seed_coze_workflow(postgres_db_url, "wf-sync", "Sync Flow", _minimal_canvas("sync-b"))

        second = sync_engine.execute_sync(db, config)
        histories = db.query(SyncHistory).order_by(SyncHistory.id.asc()).all()

    workflow = reader.read_workflow(str(app_id))

    assert first["summary"] == {
        "created": 1,
        "updated": 0,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert second["summary"] == {
        "created": 0,
        "updated": 1,
        "failed": 0,
        "skipped": 0,
        "unsupported": 0,
        "conflicts": 0,
    }
    assert len(histories) == 2
    assert histories[0].workflows_synced == 1
    assert histories[1].workflows_synced == 1
    assert workflow is not None
    assert {node["id"] for node in workflow["graph"]["nodes"]} == {"sync-b-start", "sync-b-end"}

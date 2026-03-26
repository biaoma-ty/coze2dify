from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from db.database import Base
from db.models import SyncConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _alembic_config(db_url: str) -> Config:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def test_sync_config_db_urls_are_encrypted_at_rest(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'coze2dify-encrypted-sync-config.db'}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    plain_coze_db_url = "postgresql://coze.test/app"
    plain_dify_db_url = "postgresql://dify.test/app"

    with session_factory() as db:
        config = SyncConfig(
            name="Encrypted Sync",
            coze_db_url=plain_coze_db_url,
            dify_db_url=plain_dify_db_url,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

        assert config.coze_db_url == plain_coze_db_url
        assert config.dify_db_url == plain_dify_db_url

    with engine.connect() as conn:
        row = conn.execute(text("SELECT coze_db_url, dify_db_url FROM sync_configs")).one()

    assert row.coze_db_url != plain_coze_db_url
    assert row.dify_db_url != plain_dify_db_url
    assert row.coze_db_url.startswith("enc:")
    assert row.dify_db_url.startswith("enc:")

    engine.dispose()


def test_sync_config_reads_legacy_plaintext_rows(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'coze2dify-legacy-plaintext.db'}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    plain_coze_db_url = "postgresql://legacy-coze.test/app"
    plain_dify_db_url = "postgresql://legacy-dify.test/app"

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sync_configs (
                    name,
                    coze_db_type,
                    coze_db_url,
                    dify_db_url,
                    sync_mode,
                    delete_mode,
                    enabled,
                    created_at,
                    updated_at
                ) VALUES (
                    :name,
                    :coze_db_type,
                    :coze_db_url,
                    :dify_db_url,
                    :sync_mode,
                    :delete_mode,
                    :enabled,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "name": "Legacy Sync",
                "coze_db_type": "postgresql",
                "coze_db_url": plain_coze_db_url,
                "dify_db_url": plain_dify_db_url,
                "sync_mode": "manual",
                "delete_mode": "observe_only",
                "enabled": True,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
            },
        )

    with session_factory() as db:
        config = db.execute(select(SyncConfig)).scalars().one()
        assert config.coze_db_url == plain_coze_db_url
        assert config.dify_db_url == plain_dify_db_url

    engine.dispose()


def test_alembic_upgrade_encrypts_existing_sync_config_db_urls(tmp_path) -> None:
    db_path = tmp_path / "coze2dify-alembic-encryption.db"
    db_url = f"sqlite:///{db_path}"
    config = _alembic_config(db_url)

    command.upgrade(config, "20260310_02")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sync_configs (
                    name,
                    coze_db_type,
                    coze_db_url,
                    dify_db_url,
                    sync_mode,
                    delete_mode,
                    enabled,
                    created_at,
                    updated_at
                ) VALUES (
                    :name,
                    :coze_db_type,
                    :coze_db_url,
                    :dify_db_url,
                    :sync_mode,
                    :delete_mode,
                    :enabled,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "name": "Alembic Legacy Sync",
                "coze_db_type": "postgresql",
                "coze_db_url": "postgresql://coze.alembic/app",
                "dify_db_url": "postgresql://dify.alembic/app",
                "sync_mode": "manual",
                "delete_mode": "observe_only",
                "enabled": True,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
            },
        )

    command.upgrade(config, "head")

    with engine.connect() as conn:
        row = conn.execute(text("SELECT coze_db_url, dify_db_url FROM sync_configs")).one()

    assert row.coze_db_url.startswith("enc:")
    assert row.dify_db_url.startswith("enc:")

    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as db:
        config_row = db.execute(select(SyncConfig)).scalars().one()

    assert config_row.coze_db_url == "postgresql://coze.alembic/app"
    assert config_row.dify_db_url == "postgresql://dify.alembic/app"

    engine.dispose()

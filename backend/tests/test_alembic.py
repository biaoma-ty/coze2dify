from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


PROJECT_TABLES = {"migration_tasks", "sync_configs", "sync_histories"}


def _alembic_config(db_url: str) -> Config:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def test_alembic_upgrade_and_downgrade_round_trip(tmp_path) -> None:
    db_path = tmp_path / "coze2dify-alembic.db"
    db_url = f"sqlite:///{db_path}"
    config = _alembic_config(db_url)

    command.upgrade(config, "head")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    upgraded_tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert PROJECT_TABLES.issubset(upgraded_tables)
    assert "alembic_version" in upgraded_tables

    command.downgrade(config, "base")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    downgraded_tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert PROJECT_TABLES.isdisjoint(downgraded_tables)

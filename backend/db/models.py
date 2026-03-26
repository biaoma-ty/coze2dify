from datetime import datetime, timezone

from sqlalchemy import JSON, TEXT, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.security.db_url_crypto import EncryptedDatabaseUrl

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SyncConfig(Base):
    __tablename__ = "sync_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    coze_db_type: Mapped[str] = mapped_column(String(50), default="postgresql")
    coze_db_url: Mapped[str] = mapped_column(EncryptedDatabaseUrl())
    dify_db_url: Mapped[str] = mapped_column(EncryptedDatabaseUrl())
    sync_mode: Mapped[str] = mapped_column(String(50), default="manual")
    delete_mode: Mapped[str] = mapped_column(String(50), default="observe_only")
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    tasks: Mapped[list["MigrationTask"]] = relationship(back_populates="sync_config")
    histories: Mapped[list["SyncHistory"]] = relationship(back_populates="sync_config")


class MigrationTask(Base):
    __tablename__ = "migration_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_config_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sync_configs.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50))
    source_workflow_id: Mapped[str] = mapped_column(String(255))
    source_workflow_name: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    ir_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dify_dsl: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sync_config: Mapped[SyncConfig | None] = relationship(back_populates="tasks")


class SyncHistory(Base):
    __tablename__ = "sync_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("sync_configs.id"))
    trigger_type: Mapped[str] = mapped_column(String(50))
    workflows_synced: Mapped[int] = mapped_column(Integer, default=0)
    workflows_failed: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_count: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_resolved: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")

    sync_config: Mapped[SyncConfig] = relationship(back_populates="histories")

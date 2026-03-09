"""Initial project schema.

Revision ID: 20260309_01
Revises:
Create Date: 2026-03-09 23:59:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260309_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("coze_db_type", sa.String(length=50), nullable=False),
        sa.Column("coze_db_url", sa.String(length=500), nullable=False),
        sa.Column("dify_db_url", sa.String(length=500), nullable=False),
        sa.Column("sync_mode", sa.String(length=50), nullable=False),
        sa.Column("cron_expression", sa.String(length=100), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "migration_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sync_config_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_workflow_id", sa.String(length=255), nullable=False),
        sa.Column("source_workflow_name", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("ir_snapshot", sa.JSON(), nullable=True),
        sa.Column("dify_dsl", sa.TEXT(), nullable=True),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sync_config_id"], ["sync_configs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sync_histories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sync_config_id", sa.Integer(), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("workflows_synced", sa.Integer(), nullable=False),
        sa.Column("workflows_failed", sa.Integer(), nullable=False),
        sa.Column("conflicts_count", sa.Integer(), nullable=False),
        sa.Column("conflicts_resolved", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["sync_config_id"], ["sync_configs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sync_histories")
    op.drop_table("migration_tasks")
    op.drop_table("sync_configs")

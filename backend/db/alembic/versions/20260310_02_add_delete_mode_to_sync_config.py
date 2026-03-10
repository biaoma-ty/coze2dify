"""Add delete_mode to sync configs.

Revision ID: 20260310_02
Revises: 20260309_01
Create Date: 2026-03-10 10:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260310_02"
down_revision = "20260309_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sync_configs",
        sa.Column("delete_mode", sa.String(length=50), nullable=False, server_default="observe_only"),
    )


def downgrade() -> None:
    op.drop_column("sync_configs", "delete_mode")

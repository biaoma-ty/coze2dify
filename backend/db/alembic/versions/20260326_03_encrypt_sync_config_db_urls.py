"""Encrypt persisted sync config database URLs.

Revision ID: 20260326_03
Revises: 20260310_02
Create Date: 2026-03-26 18:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from core.security.db_url_crypto import decrypt_database_url, encrypt_database_url


# revision identifiers, used by Alembic.
revision = "20260326_03"
down_revision = "20260310_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sync_configs") as batch_op:
        batch_op.alter_column(
            "coze_db_url",
            existing_type=sa.String(length=500),
            type_=sa.Text(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "dify_db_url",
            existing_type=sa.String(length=500),
            type_=sa.Text(),
            existing_nullable=False,
        )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, coze_db_url, dify_db_url FROM sync_configs")).mappings().all()
    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE sync_configs
                SET coze_db_url = :coze_db_url,
                    dify_db_url = :dify_db_url
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "coze_db_url": encrypt_database_url(row["coze_db_url"]),
                "dify_db_url": encrypt_database_url(row["dify_db_url"]),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, coze_db_url, dify_db_url FROM sync_configs")).mappings().all()
    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE sync_configs
                SET coze_db_url = :coze_db_url,
                    dify_db_url = :dify_db_url
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "coze_db_url": decrypt_database_url(row["coze_db_url"]),
                "dify_db_url": decrypt_database_url(row["dify_db_url"]),
            },
        )

    with op.batch_alter_table("sync_configs") as batch_op:
        batch_op.alter_column(
            "coze_db_url",
            existing_type=sa.Text(),
            type_=sa.String(length=500),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "dify_db_url",
            existing_type=sa.Text(),
            type_=sa.String(length=500),
            existing_nullable=False,
        )

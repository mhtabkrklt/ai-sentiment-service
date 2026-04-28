# Версионирование данных
"""create analyses table

Revision ID: 0001
Revises:
Create Date: 2026-04-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("label", sa.String(10), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("all_scores", JSON(), nullable=False),
        sa.Column("elapsed_ms", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("analyses")

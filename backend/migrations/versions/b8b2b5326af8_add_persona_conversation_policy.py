"""add persona conversation_policy

Revision ID: b8b2b5326af8
Revises: a1f4c9d2e7b3
Create Date: 2026-08-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembicが使うリビジョン識別子
revision: str = "b8b2b5326af8"
down_revision: str | Sequence[str] | None = "a1f4c9d2e7b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """スキーマをこのリビジョンの状態へ進める。"""
    op.add_column(
        "m_persona", sa.Column("conversation_policy", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """スキーマを1つ前のリビジョンの状態へ戻す。"""
    op.drop_column("m_persona", "conversation_policy")

"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

# Alembicが使うリビジョン識別子
revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """スキーマをこのリビジョンの状態へ進める。"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """スキーマを1つ前のリビジョンの状態へ戻す。"""
    ${downgrades if downgrades else "pass"}

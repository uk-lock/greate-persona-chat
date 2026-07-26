"""ユーザ（m_user）のSQLAlchemyモデル。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.chat import Chat


class User(AuditMixin, Base):
    """ログインユーザ。認証情報とログイン失敗ロック状態を保持する。"""

    __tablename__ = "m_user"

    login_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    chats: Mapped[list["Chat"]] = relationship(back_populates="user", lazy="raise")

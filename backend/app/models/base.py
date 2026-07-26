"""SQLAlchemyモデル共通の土台（declarative base・監査カラムmixin）を定義するモジュール。"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """全モデル共通のdeclarative base。"""


class AuditMixin:
    """全テーブル共通の主キー・監査カラムを提供するmixin。

    id / is_deleted / created_at / updated_at / created_by / updated_by は
    db.mdの全テーブルで共通のため、テーブルごとの重複定義を避けるためにここへ集約する。
    """

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)

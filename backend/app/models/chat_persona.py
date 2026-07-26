"""チャットとペルソナの中間テーブル（t_chat_persona）のSQLAlchemyモデル。"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.persona import Persona


class ChatPersona(AuditMixin, Base):
    """チャットへのペルソナの参加情報（表示順・発言順を含む）。"""

    __tablename__ = "t_chat_persona"
    __table_args__ = (UniqueConstraint("chat_id", "sort_no"),)

    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("t_chat.id"), nullable=False
    )
    persona_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("m_persona.id"), nullable=False
    )
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="chat_personas", lazy="raise")
    persona: Mapped["Persona"] = relationship(
        back_populates="chat_personas", lazy="raise"
    )

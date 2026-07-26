"""チャットメッセージ（t_chat_message）のSQLAlchemyモデル。"""

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.chat import Chat
    from app.models.persona import Persona


class SpeakerType(StrEnum):
    """メッセージの発話者種別。"""

    USER = "USER"
    PERSONA = "PERSONA"


class ChatMessage(AuditMixin, Base):
    """チャット内の1発言。

    speaker_typeが PERSONA の場合は persona_id が必須、USER の場合は
    persona_id は NULL とする（db.md参照）。この対応関係の妥当性検証は
    サービス層の責務とし、モデル上は persona_id を任意項目として扱う。
    """

    __tablename__ = "t_chat_message"
    __table_args__ = (UniqueConstraint("chat_id", "sort_no"),)

    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("t_chat.id"), nullable=False
    )
    persona_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("m_persona.id"), nullable=True
    )
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_type: Mapped[SpeakerType] = mapped_column(
        SAEnum(SpeakerType, native_enum=False, length=50), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)

    chat: Mapped["Chat"] = relationship(back_populates="messages", lazy="raise")
    persona: Mapped["Persona | None"] = relationship(
        back_populates="chat_messages", lazy="raise"
    )

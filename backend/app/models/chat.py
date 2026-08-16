"""チャット（t_chat）のSQLAlchemyモデル。"""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.chat_persona import ChatPersona
    from app.models.user import User


class ChatMode(StrEnum):
    """チャットの進行モード。"""

    PERSONA_ONLY = "PERSONA_ONLY"
    USER_PARTICIPATED = "USER_PARTICIPATED"


class Chat(AuditMixin, Base):
    """ユーザとペルソナによるチャットセッション。"""

    __tablename__ = "t_chat"

    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4
    )
    """外部公開用のチャットID（URL・APIレスポンスで使用）。

    内部PK（id、BIGINT）は他テーブルとのFK関係でそのまま使い続け、外部に見せる識別子だけ
    連番から推測されないUUIDに分離する（t_chat_message・t_chat_personaのFK型は変更しない）。
    """

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("m_user.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chat_mode: Mapped[ChatMode] = mapped_column(
        SAEnum(ChatMode, native_enum=False, length=50), nullable=False
    )
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """会話のお題（PERSONA_ONLYモードのみ必須。USER_PARTICIPATEDではNULL）。

    履歴が流れても方向性が失われないよう、LLMグラフのsystem promptへ毎ターン
    差し込む（app/llm/nodes.py参照）。DBレベルでは`chat_mode`依存の必須制約を
    表現できないため、CHECK制約は設けずAPI層（CreateChatRequest）で検証する。
    """
    is_stopped: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    user: Mapped["User"] = relationship(back_populates="chats", lazy="raise")
    chat_personas: Mapped[list["ChatPersona"]] = relationship(
        back_populates="chat", order_by="ChatPersona.sort_no", lazy="raise"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="chat", order_by="ChatMessage.sort_no", lazy="raise"
    )

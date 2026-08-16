"""ペルソナ（m_persona）のSQLAlchemyモデル。"""

from typing import TYPE_CHECKING, TypedDict

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.chat_persona import ChatPersona


class BiographyEntry(TypedDict):
    """biographyの年表1件分（例：`{"year": 1780, "event": "XXXをした"}`）。"""

    year: int
    event: str


class Persona(AuditMixin, Base):
    """偉人ペルソナのプロフィール情報。"""

    __tablename__ = "m_persona"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    era: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    conversation_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    biography: Mapped[list[BiographyEntry] | None] = mapped_column(JSONB, nullable=True)
    sample_quotes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    chat_personas: Mapped[list["ChatPersona"]] = relationship(
        back_populates="persona", lazy="raise"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="persona", lazy="raise"
    )

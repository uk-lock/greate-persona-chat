"""チャット関連のリクエスト/レスポンススキーマ。"""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.config.constants import (
    CHAT_PERSONA_MAX_COUNT,
    CHAT_PERSONA_MIN_COUNT,
    USER_MESSAGE_MAX_LENGTH,
)
from app.models.chat import ChatMode
from app.models.chat_message import SpeakerType


class UserParticipant(BaseModel):
    """チャット参加者のうちユーザー本人を表す要素。"""

    type: Literal["USER"]
    name: str


class PersonaParticipant(BaseModel):
    """チャット参加者のうちペルソナを表す要素。"""

    type: Literal["PERSONA"]
    persona_id: int
    name: str
    image_url: str | None


Participant = Annotated[
    UserParticipant | PersonaParticipant, Field(discriminator="type")
]


class ChatResponse(BaseModel):
    """チャット一覧・作成のレスポンス（`GET /chats`・`POST /chats`）。

    participantsの合成（USER_PARTICIPATEDの場合の「あなた」要素の付与等）が
    必要なため、from_attributesによる自動変換は行わずルーター側で組み立てる。

    chat_idは外部公開用ID（t_chat.public_id、UUID）であり、内部PK（BIGINT）とは
    別物（app/models/chat.py参照）。
    """

    chat_id: uuid.UUID
    title: str
    chat_mode: ChatMode
    updated_at: datetime
    participants: list[Participant]


class CreateChatRequest(BaseModel):
    """チャット作成リクエスト（`POST /chats`）。"""

    persona_ids: list[int]
    chat_mode: ChatMode

    @field_validator("persona_ids")
    @classmethod
    def validate_persona_count(cls, value: list[int]) -> list[int]:
        """参加ペルソナ数が設定値の範囲内であることを検証する。"""
        if not CHAT_PERSONA_MIN_COUNT <= len(value) <= CHAT_PERSONA_MAX_COUNT:
            raise ValueError(
                f"ペルソナは{CHAT_PERSONA_MIN_COUNT}〜{CHAT_PERSONA_MAX_COUNT}体選択してください"
            )
        return value


class ChatMessageResponse(BaseModel):
    """チャットメッセージのレスポンス（`GET /chats/{chat_id}/messages`・SSEイベント）。"""

    model_config = {"from_attributes": True}

    id: int
    sort_no: int
    speaker_type: SpeakerType
    persona_id: int | None
    message: str
    created_at: datetime


class PostMessageRequest(BaseModel):
    """メッセージ送信リクエスト（`POST /chats/{chat_id}/messages`）。

    PERSONA_ONLYモードでは本文なし（`message=None`）で送信される。
    USER_PARTICIPATEDモードでの必須チェックはchat_modeに依存するため
    サービス層（ChatService.save_user_message）で行う。
    """

    message: str | None = Field(default=None, max_length=USER_MESSAGE_MAX_LENGTH)


class ThinkingEvent(BaseModel):
    """ペルソナが選ばれ、応答を生成中であることを示すSSEイベント。"""

    type: Literal["thinking"] = "thinking"
    persona_id: int


class MessageEvent(BaseModel):
    """ペルソナ・ユーザーの発言が1件完成したことを示すSSEイベント。"""

    type: Literal["message"] = "message"
    message: ChatMessageResponse


class TitleEvent(BaseModel):
    """チャットタイトルが自動生成・更新されたことを示すSSEイベント。"""

    type: Literal["title"] = "title"
    title: str


class ErrorEvent(BaseModel):
    """会話進行中にエラーが発生し、ストリームを終了することを示すSSEイベント。"""

    type: Literal["error"] = "error"
    message: str


ChatStreamEvent = Annotated[
    ThinkingEvent | MessageEvent | TitleEvent | ErrorEvent,
    Field(discriminator="type"),
]
"""`POST /chats/{chat_id}/messages`のSSEイベント（判別ユニオン）。"""

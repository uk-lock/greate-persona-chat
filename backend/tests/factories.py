"""テストで使うSQLAlchemyモデルのビルダー関数。

DBセッションを介さずインメモリでモデルを組み立てるための共通ヘルパー。
各テストが必要な項目だけ`overrides`で上書きできるようにし、
`AuditMixin`由来の定型項目（id・is_deleted・created_by・updated_by等）の
ボイラープレートをテストコードから排除する。
"""

import uuid
from typing import Any

from app.models.chat import Chat, ChatMode
from app.models.chat_message import ChatMessage, SpeakerType
from app.models.chat_persona import ChatPersona
from app.models.persona import Persona
from app.models.user import User


def make_user(**overrides: Any) -> User:
    defaults: dict[str, Any] = {
        "id": 1,
        "login_id": "alice",
        "password_hash": "dummy-hash",
        "failed_login_count": 0,
        "locked_until": None,
        "is_deleted": False,
        "created_by": "alice",
        "updated_by": "alice",
    }
    defaults.update(overrides)
    return User(**defaults)


def make_persona(**overrides: Any) -> Persona:
    defaults: dict[str, Any] = {
        "id": 1,
        "name": "ソクラテス",
        "image_url": None,
        "country": "ギリシャ",
        "era": "古代",
        "summary": None,
        "description": None,
        "personality": None,
        "conversation_policy": None,
        "biography": None,
        "sample_quotes": None,
        "is_deleted": False,
        "created_by": "system",
        "updated_by": "system",
    }
    defaults.update(overrides)
    return Persona(**defaults)


def make_chat(**overrides: Any) -> Chat:
    defaults: dict[str, Any] = {
        "id": 10,
        "public_id": uuid.uuid4(),
        "user_id": 1,
        "title": "新規チャット",
        "chat_mode": ChatMode.PERSONA_ONLY,
        "topic": "哲学について",
        "is_stopped": False,
        "is_deleted": False,
        "created_by": "alice",
        "updated_by": "alice",
        "chat_personas": [],
    }
    defaults.update(overrides)
    return Chat(**defaults)


def make_chat_persona(**overrides: Any) -> ChatPersona:
    defaults: dict[str, Any] = {
        "id": 100,
        "chat_id": 10,
        "persona_id": 1,
        "sort_no": 1,
        "is_deleted": False,
        "created_by": "alice",
        "updated_by": "alice",
        "persona": None,
    }
    defaults.update(overrides)
    return ChatPersona(**defaults)


def make_chat_message(**overrides: Any) -> ChatMessage:
    defaults: dict[str, Any] = {
        "id": 1000,
        "chat_id": 10,
        "persona_id": None,
        "sort_no": 1,
        "speaker_type": SpeakerType.USER,
        "message": "こんにちは",
        "is_deleted": False,
        "created_by": "alice",
        "updated_by": "alice",
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)

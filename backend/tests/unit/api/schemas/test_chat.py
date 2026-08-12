"""`app/api/schemas/chat.py`の単体テスト。

`CreateChatRequest`のバリデータ（ペルソナ数の範囲・chat_modeとtopicの組み合わせ）を検証する。
"""

import pytest
from pydantic import ValidationError

from app.api.schemas.chat import CreateChatRequest
from app.config.constants import CHAT_PERSONA_MAX_COUNT, CHAT_PERSONA_MIN_COUNT
from app.models.chat import ChatMode


def _request(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "persona_ids": [1],
        "chat_mode": ChatMode.USER_PARTICIPATED,
        "topic": None,
    }
    base.update(overrides)
    return base


class TestValidatePersonaCount:
    def test_below_min_count_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            CreateChatRequest.model_validate(
                _request(persona_ids=list(range(CHAT_PERSONA_MIN_COUNT - 1)))
            )

    def test_min_count_boundary_is_valid(self) -> None:
        CreateChatRequest.model_validate(
            _request(persona_ids=list(range(CHAT_PERSONA_MIN_COUNT)))
        )

    def test_max_count_boundary_is_valid(self) -> None:
        CreateChatRequest.model_validate(
            _request(persona_ids=list(range(CHAT_PERSONA_MAX_COUNT)))
        )

    def test_above_max_count_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            CreateChatRequest.model_validate(
                _request(persona_ids=list(range(CHAT_PERSONA_MAX_COUNT + 1)))
            )


class TestValidateTopicByChatMode:
    def test_persona_only_without_topic_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            CreateChatRequest.model_validate(
                _request(chat_mode=ChatMode.PERSONA_ONLY, topic=None)
            )

    def test_persona_only_with_topic_is_valid(self) -> None:
        CreateChatRequest.model_validate(
            _request(chat_mode=ChatMode.PERSONA_ONLY, topic="哲学について")
        )

    def test_user_participated_without_topic_is_valid(self) -> None:
        CreateChatRequest.model_validate(
            _request(chat_mode=ChatMode.USER_PARTICIPATED, topic=None)
        )

    def test_user_participated_with_topic_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            CreateChatRequest.model_validate(
                _request(chat_mode=ChatMode.USER_PARTICIPATED, topic="哲学について")
            )

"""`app/api/routers/chats.py`のうち、DB・実LLMに依存しない純粋なロジックの単体テスト。

`chat_service`はフェイクの非同期ジェネレータに差し替え、実DB・実LLM APIには一切依存しない。
エンドポイント本体（DI配線込みの一連の流れ）はIT側で担保するため対象外とする。
"""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock

from app.api.routers.chats import _build_chat_response, _format_sse_event, _stream_turns
from app.api.schemas.chat import PersonaParticipant, ThinkingEvent, UserParticipant
from app.models.chat import ChatMode
from app.services.chat_service import (
    MessageTurnEvent,
    ThinkingTurnEvent,
    TitleTurnEvent,
    TurnEvent,
)
from app.services.exceptions import ExternalServiceError
from tests.factories import (
    make_chat,
    make_chat_message,
    make_chat_persona,
    make_persona,
    make_user,
)


def _parse(chunk: bytes) -> dict[str, object]:
    text = chunk.decode()
    assert text.startswith("data: ")
    assert text.endswith("\n\n")
    return json.loads(text[len("data: ") : -2])


class TestBuildChatResponse:
    def test_user_participated_includes_user_participant_first(self) -> None:
        persona = make_persona(
            id=1, name="ソクラテス", image_url="http://example.com/1.png"
        )
        chat_persona = make_chat_persona(persona_id=1, persona=persona)
        chat = make_chat(
            chat_mode=ChatMode.USER_PARTICIPATED,
            chat_personas=[chat_persona],
            updated_at=datetime.now(UTC),
        )

        response = _build_chat_response(chat)

        assert response.participants[0] == UserParticipant(type="USER", name="あなた")
        assert response.participants[1] == PersonaParticipant(
            type="PERSONA",
            persona_id=1,
            name="ソクラテス",
            image_url="http://example.com/1.png",
        )

    def test_persona_only_excludes_user_participant(self) -> None:
        persona = make_persona(id=2, name="プラトン", image_url=None)
        chat_persona = make_chat_persona(persona_id=2, persona=persona)
        chat = make_chat(
            chat_mode=ChatMode.PERSONA_ONLY,
            chat_personas=[chat_persona],
            updated_at=datetime.now(UTC),
        )

        response = _build_chat_response(chat)

        assert response.participants == [
            PersonaParticipant(
                type="PERSONA", persona_id=2, name="プラトン", image_url=None
            )
        ]

    def test_maps_basic_fields(self) -> None:
        chat = make_chat(
            title="哲学談義",
            chat_mode=ChatMode.PERSONA_ONLY,
            topic="哲学について",
            chat_personas=[],
            updated_at=datetime.now(UTC),
        )

        response = _build_chat_response(chat)

        assert response.chat_id == chat.public_id
        assert response.title == "哲学談義"
        assert response.chat_mode == ChatMode.PERSONA_ONLY
        assert response.topic == "哲学について"


class TestFormatSseEvent:
    def test_formats_as_sse_data_frame(self) -> None:
        event = ThinkingEvent(persona_id=1)

        result = _format_sse_event(event)

        assert result == f"data: {event.model_dump_json()}\n\n".encode()


def _fake_chat_service(events: list[TurnEvent | Exception]) -> MagicMock:
    async def _stream_turns_stub(
        *args: object, **kwargs: object
    ) -> AsyncIterator[TurnEvent]:
        for event in events:
            if isinstance(event, Exception):
                raise event
            yield event

    chat_service = MagicMock()
    chat_service.stream_turns = _stream_turns_stub
    return chat_service


class TestStreamTurns:
    async def test_yields_message_event_first_when_user_message_given(self) -> None:
        user_message = make_chat_message(
            id=1, message="こんにちは", created_at=datetime.now(UTC)
        )
        chat_service = _fake_chat_service([])

        chunks = [
            chunk
            async for chunk in _stream_turns(
                10,
                make_user(),
                ChatMode.USER_PARTICIPATED,
                MagicMock(),
                chat_service,
                user_message,
            )
        ]

        assert len(chunks) == 1
        parsed = _parse(chunks[0])
        assert parsed["type"] == "message"
        assert cast(dict[str, object], parsed["message"])["id"] == 1

    async def test_no_message_event_when_user_message_is_none(self) -> None:
        chat_service = _fake_chat_service([])

        chunks = [
            chunk
            async for chunk in _stream_turns(
                10, make_user(), ChatMode.PERSONA_ONLY, MagicMock(), chat_service, None
            )
        ]

        assert chunks == []

    async def test_converts_thinking_message_and_title_turn_events(self) -> None:
        persona = make_persona(id=5)
        message = make_chat_message(
            id=2, persona_id=5, message="やあ", created_at=datetime.now(UTC)
        )
        chat_service = _fake_chat_service(
            [
                ThinkingTurnEvent(persona=persona),
                MessageTurnEvent(message=message),
                TitleTurnEvent(title="新しい会話"),
            ]
        )

        chunks = [
            chunk
            async for chunk in _stream_turns(
                10, make_user(), ChatMode.PERSONA_ONLY, MagicMock(), chat_service, None
            )
        ]

        assert [_parse(chunk)["type"] for chunk in chunks] == [
            "thinking",
            "message",
            "title",
        ]
        assert _parse(chunks[0])["persona_id"] == 5
        assert cast(dict[str, object], _parse(chunks[1])["message"])["id"] == 2
        assert _parse(chunks[2])["title"] == "新しい会話"

    async def test_external_service_error_yields_error_event_and_ends_stream(
        self,
    ) -> None:
        chat_service = _fake_chat_service(
            [
                ThinkingTurnEvent(persona=make_persona(id=1)),
                ExternalServiceError("応答の生成に失敗しました"),
            ]
        )

        chunks = [
            chunk
            async for chunk in _stream_turns(
                10, make_user(), ChatMode.PERSONA_ONLY, MagicMock(), chat_service, None
            )
        ]

        assert [_parse(chunk)["type"] for chunk in chunks] == ["thinking", "error"]
        assert _parse(chunks[1])["message"] == "応答の生成に失敗しました"

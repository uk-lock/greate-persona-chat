"""ChatService（チャット・チャットメッセージ）の単体テスト。

各Repositoryおよび`ChatGraph`はAsyncMock／スタブに置き換え、実DB・実LLM APIには
一切依存しない。`ChatGraph.astream`は「（node_name, delta）の並びを返す
非同期ジェネレータ」という契約のみを満たせばよいため、`_FakeChatGraph`という
軽量スタブで代替する（AsyncMockは非同期ジェネレータの表現に不向きなため）。
"""

import uuid
from collections.abc import AsyncIterator
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config.constants import DEFAULT_CHAT_TITLE
from app.llm.graph import ChatGraph
from app.models.chat import ChatMode
from app.models.chat_message import SpeakerType
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_persona_repository import ChatPersonaRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.persona_repository import PersonaRepository
from app.services.chat_service import (
    ChatService,
    MessageTurnEvent,
    ThinkingTurnEvent,
    TitleTurnEvent,
)
from app.services.exceptions import (
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from tests.factories import make_chat, make_chat_persona, make_persona, make_user


class _FakeChatGraph:
    """`ChatGraph.astream`の入出力契約のみを満たすテスト用スタブ。

    `chunks`には`{node_name: delta}`のdict、またはBaseExceptionを渡す。
    BaseExceptionの場合はストリーム途中でその例外を送出する。
    """

    def __init__(self, chunks: list) -> None:
        self._chunks = chunks
        self.calls: list[dict] = []

    async def astream(
        self, initial_state, *, context, stream_mode
    ) -> AsyncIterator[dict]:
        self.calls.append(
            {
                "initial_state": initial_state,
                "context": context,
                "stream_mode": stream_mode,
            }
        )
        for chunk in self._chunks:
            if isinstance(chunk, BaseException):
                raise chunk
            yield chunk


class _FakeApiError(Exception):
    """LLMプロバイダのAPIStatusError系を模した例外（`status_code`属性を持つ）。"""

    status_code = 500


@pytest.fixture
def chat_repository() -> AsyncMock:
    return AsyncMock(spec=ChatRepository)


@pytest.fixture
def chat_persona_repository() -> AsyncMock:
    return AsyncMock(spec=ChatPersonaRepository)


@pytest.fixture
def chat_message_repository() -> AsyncMock:
    return AsyncMock(spec=ChatMessageRepository)


@pytest.fixture
def persona_repository() -> AsyncMock:
    return AsyncMock(spec=PersonaRepository)


@pytest.fixture
def chat_graph() -> MagicMock:
    """stream_turns以外のテストでは使われないため、汎用のMagicMockで十分。"""
    return MagicMock()


@pytest.fixture
def chat_service(
    chat_repository: AsyncMock,
    chat_persona_repository: AsyncMock,
    chat_message_repository: AsyncMock,
    persona_repository: AsyncMock,
    chat_graph: MagicMock,
) -> ChatService:
    return ChatService(
        chat_repository,
        chat_persona_repository,
        chat_message_repository,
        persona_repository,
        chat_graph,
    )


@pytest.fixture
def current_user():
    return make_user(id=1, login_id="alice")


class TestResolveInternalId:
    async def test_returns_internal_id_when_found(
        self, chat_service: ChatService, chat_repository: AsyncMock
    ) -> None:
        chat = make_chat(id=10)
        chat_repository.get_by_public_id.return_value = chat

        result = await chat_service.resolve_internal_id(chat.public_id)

        assert result == 10

    async def test_raises_not_found_when_missing(
        self, chat_service: ChatService, chat_repository: AsyncMock
    ) -> None:
        chat_repository.get_by_public_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.resolve_internal_id(uuid.uuid4())


class TestGetByUser:
    async def test_returns_chats_from_repository(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chats = [make_chat(id=1), make_chat(id=2)]
        chat_repository.get_by_user.return_value = chats

        result = await chat_service.get_by_user(current_user)

        assert result == chats

    async def test_returns_empty_list_when_no_chat(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_user.return_value = []

        result = await chat_service.get_by_user(current_user)

        assert result == []


class TestCreate:
    async def test_creates_chat_and_chat_personas_in_order(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        persona_repository.get_by_id.side_effect = [
            make_persona(id=1),
            make_persona(id=2),
        ]
        created_chat = make_chat(id=10)
        chat_repository.add.return_value = created_chat
        chat_repository.get_by_id.return_value = created_chat

        result = await chat_service.create(
            current_user, [1, 2], ChatMode.PERSONA_ONLY, "お題"
        )

        assert result is created_chat
        added_chat = chat_repository.add.call_args.args[0]
        assert added_chat.title == DEFAULT_CHAT_TITLE
        assert added_chat.chat_mode == ChatMode.PERSONA_ONLY
        assert added_chat.topic == "お題"
        assert added_chat.is_stopped is False
        assert added_chat.created_by == current_user.login_id
        assert added_chat.updated_by == current_user.login_id

        chat_personas = chat_persona_repository.add_all.call_args.args[0]
        assert [cp.persona_id for cp in chat_personas] == [1, 2]
        assert [cp.sort_no for cp in chat_personas] == [1, 2]
        assert all(cp.chat_id == created_chat.id for cp in chat_personas)

    async def test_raises_not_found_and_stops_at_first_missing_persona(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        persona_repository.get_by_id.side_effect = [make_persona(id=1), None]

        with pytest.raises(NotFoundError):
            await chat_service.create(
                current_user, [1, 2, 3], ChatMode.PERSONA_ONLY, "お題"
            )

        assert persona_repository.get_by_id.await_count == 2
        chat_repository.add.assert_not_awaited()

    async def test_allows_empty_persona_ids(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        """空配列（サービス単体では件数バリデーションを行わない）。

        件数チェック自体はAPI層のスキーマ（CreateChatRequest）が担うため、
        サービス単体はこの前提を置いた素通り挙動になる。
        """
        created_chat = make_chat(id=11)
        chat_repository.add.return_value = created_chat
        chat_repository.get_by_id.return_value = created_chat

        result = await chat_service.create(
            current_user, [], ChatMode.PERSONA_ONLY, "お題"
        )

        assert result is created_chat
        persona_repository.get_by_id.assert_not_awaited()
        chat_persona_repository.add_all.assert_awaited_once_with([])

    async def test_allows_duplicate_persona_ids(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        """重複するpersona_idも現状は拒否せずそのまま登録される（現状仕様として固定）。"""
        persona = make_persona(id=1)
        persona_repository.get_by_id.side_effect = [persona, persona]
        created_chat = make_chat(id=12)
        chat_repository.add.return_value = created_chat
        chat_repository.get_by_id.return_value = created_chat

        await chat_service.create(current_user, [1, 1], ChatMode.PERSONA_ONLY, "お題")

        chat_personas = chat_persona_repository.add_all.call_args.args[0]
        assert [cp.persona_id for cp in chat_personas] == [1, 1]
        assert [cp.sort_no for cp in chat_personas] == [1, 2]

    async def test_raises_not_found_when_created_chat_cannot_be_refetched(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        """flush直後のchatが再取得できない防御分岐。"""
        persona_repository.get_by_id.return_value = make_persona(id=1)
        chat_repository.add.return_value = make_chat(id=13)
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.create(current_user, [1], ChatMode.PERSONA_ONLY, "お題")


class TestDelete:
    async def test_marks_chat_as_deleted(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id, is_deleted=False)
        chat_repository.get_by_id.return_value = chat

        await chat_service.delete(10, current_user)

        assert chat.is_deleted is True
        assert chat.updated_by == current_user.login_id
        chat_repository.flush.assert_awaited_once()

    async def test_raises_not_found_when_missing(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.delete(999, current_user)

    async def test_raises_forbidden_when_not_owner(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id + 1)
        chat_repository.get_by_id.return_value = chat

        with pytest.raises(ForbiddenError):
            await chat_service.delete(10, current_user)


class TestGetById:
    async def test_returns_owned_chat(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id)
        chat_repository.get_by_id.return_value = chat

        result = await chat_service.get_by_id(10, current_user)

        assert result is chat

    async def test_raises_forbidden_when_not_owner(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id + 1)
        chat_repository.get_by_id.return_value = chat

        with pytest.raises(ForbiddenError):
            await chat_service.get_by_id(10, current_user)


class TestGetChatMode:
    async def test_returns_chat_mode(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.USER_PARTICIPATED
        )
        chat_repository.get_by_id.return_value = chat

        result = await chat_service.get_chat_mode(10, current_user)

        assert result == ChatMode.USER_PARTICIPATED

    async def test_raises_not_found_when_missing(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.get_chat_mode(999, current_user)


class TestGetMessages:
    async def test_returns_messages_for_owned_chat(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id)
        chat_repository.get_by_id.return_value = chat
        chat_message_repository.get_by_chat.return_value = []

        result = await chat_service.get_messages(10, current_user)

        assert result == []
        chat_message_repository.get_by_chat.assert_awaited_once_with(10)

    async def test_raises_forbidden_when_not_owner(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id + 1)
        chat_repository.get_by_id.return_value = chat

        with pytest.raises(ForbiddenError):
            await chat_service.get_messages(10, current_user)
        chat_message_repository.get_by_chat.assert_not_awaited()


class TestStop:
    async def test_marks_chat_as_stopped(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id, is_stopped=False)
        chat_repository.get_by_id.return_value = chat

        await chat_service.stop(10, current_user)

        assert chat.is_stopped is True
        chat_repository.flush.assert_awaited_once()

    async def test_raises_not_found_when_missing(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.stop(999, current_user)


class TestSaveUserMessage:
    async def test_reactivates_stopped_chat_and_saves_message(
        self,
        chat_service: ChatService,
        chat_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id, is_stopped=True)
        chat_repository.get_by_id.return_value = chat
        chat_message_repository.get_next_sort_no.return_value = 3
        chat_message_repository.add.side_effect = lambda message: message

        result = await chat_service.save_user_message(10, current_user, "こんにちは")

        assert chat.is_stopped is False
        assert chat.updated_by == current_user.login_id
        assert result.message == "こんにちは"
        assert result.sort_no == 3
        assert result.speaker_type == SpeakerType.USER
        assert result.persona_id is None

    async def test_raises_validation_error_when_none(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = make_chat(
            id=10, user_id=current_user.id
        )

        with pytest.raises(ValidationError):
            await chat_service.save_user_message(10, current_user, None)

    async def test_raises_validation_error_when_empty_string(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = make_chat(
            id=10, user_id=current_user.id
        )

        with pytest.raises(ValidationError):
            await chat_service.save_user_message(10, current_user, "")

    async def test_raises_validation_error_when_whitespace_only(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = make_chat(
            id=10, user_id=current_user.id
        )

        with pytest.raises(ValidationError):
            await chat_service.save_user_message(10, current_user, "   ")

    async def test_raises_not_found_when_chat_missing(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await chat_service.save_user_message(999, current_user, "こんにちは")

    async def test_raises_forbidden_when_not_owner(
        self, chat_service: ChatService, chat_repository: AsyncMock, current_user
    ) -> None:
        chat_repository.get_by_id.return_value = make_chat(
            id=10, user_id=current_user.id + 1
        )

        with pytest.raises(ForbiddenError):
            await chat_service.save_user_message(10, current_user, "こんにちは")


class TestStreamTurns:
    def _make_service_with_chunks(
        self,
        chunks: list,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        chat: object,
    ) -> ChatService:
        chat_repository.get_by_id.return_value = chat
        chat_message_repository.get_by_chat.return_value = []
        chat_message_repository.get_next_sort_no.return_value = 1
        chat_message_repository.add.side_effect = lambda message: message
        return ChatService(
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            cast(ChatGraph, _FakeChatGraph(chunks)),
        )

    async def test_emits_thinking_message_and_title_events(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        persona = make_persona(id=1, name="ソクラテス")
        chat_persona = make_chat_persona(persona_id=1, sort_no=1, persona=persona)
        chat = make_chat(
            id=10,
            user_id=current_user.id,
            chat_mode=ChatMode.PERSONA_ONLY,
            title=DEFAULT_CHAT_TITLE,
            chat_personas=[chat_persona],
        )
        chunks = [
            {"select_speaker": {"current_persona_id": 1}},
            {"generate_reply": {"generated_reply_text": "こんにちは"}},
            {"maybe_update_title": {"generated_title": "新しいタイトル"}},
        ]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        events = [
            event
            async for event in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            )
        ]

        assert isinstance(events[0], ThinkingTurnEvent)
        assert events[0].persona is persona
        assert isinstance(events[1], MessageTurnEvent)
        assert events[1].message.message == "こんにちは"
        assert events[1].message.persona_id == 1
        assert isinstance(events[2], TitleTurnEvent)
        assert events[2].title == "新しいタイトル"
        assert chat.title == "新しいタイトル"
        chat_repository.flush.assert_awaited_once()

    async def test_skips_events_with_empty_delta_or_no_persona_selected(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.PERSONA_ONLY
        )
        chunks = [
            {"select_speaker": {}},
            {"select_speaker": {"current_persona_id": None}},
            {"maybe_update_title": {"generated_title": None}},
        ]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        events = [
            event
            async for event in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            )
        ]

        assert events == []
        chat_repository.flush.assert_not_awaited()

    async def test_raises_runtime_error_when_reply_arrives_before_speaker_selected(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.PERSONA_ONLY
        )
        chunks = [{"generate_reply": {"generated_reply_text": "x"}}]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        with pytest.raises(RuntimeError):
            async for _ in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

    async def test_propagates_key_error_when_selected_persona_not_a_participant(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        """グラフが参加者に含まれないpersona_idを選んだ場合、KeyErrorがそのまま伝播する

        （current_personaがNoneのまま応答生成が来た場合のRuntimeErrorと同様、
        グラフ側の不変条件違反はfail-fastとして扱う現状挙動）。
        """
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.PERSONA_ONLY
        )
        chunks = [{"select_speaker": {"current_persona_id": 999}}]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        with pytest.raises(KeyError):
            async for _ in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

    async def test_converts_llm_api_error_to_external_service_error(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.PERSONA_ONLY
        )
        chunks = [_FakeApiError("temporarily unavailable")]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        with pytest.raises(ExternalServiceError):
            async for _ in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

    async def test_reraises_non_llm_exception_as_is(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(
            id=10, user_id=current_user.id, chat_mode=ChatMode.PERSONA_ONLY
        )
        chunks = [ValueError("unexpected")]
        service = self._make_service_with_chunks(
            chunks,
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        with pytest.raises(ValueError, match="unexpected"):
            async for _ in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

    async def test_raises_not_found_when_chat_missing(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        service = self._make_service_with_chunks(
            [],
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            None,
        )
        chat_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            async for _ in service.stream_turns(
                999, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

    async def test_raises_forbidden_when_not_owner(
        self,
        chat_repository: AsyncMock,
        chat_persona_repository: AsyncMock,
        chat_message_repository: AsyncMock,
        persona_repository: AsyncMock,
        current_user,
    ) -> None:
        chat = make_chat(id=10, user_id=current_user.id + 1)
        service = self._make_service_with_chunks(
            [],
            chat_repository,
            chat_persona_repository,
            chat_message_repository,
            persona_repository,
            chat,
        )

        with pytest.raises(ForbiddenError):
            async for _ in service.stream_turns(
                10, current_user, ChatMode.PERSONA_ONLY, MagicMock()
            ):
                pass

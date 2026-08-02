"""チャット・チャットメッセージに関するユースケース。"""

import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from fastapi import Request

from app.config import constants
from app.config.constants import DEFAULT_CHAT_TITLE
from app.llm.context import ChatRunContext
from app.llm.graph import ChatGraph
from app.llm.retry import is_llm_api_error
from app.llm.state import (
    ChatTurnState,
    persona_profile_from_model,
    turn_entry_from_message,
)
from app.models.chat import Chat, ChatMode
from app.models.chat_message import ChatMessage, SpeakerType
from app.models.chat_persona import ChatPersona
from app.models.persona import Persona
from app.models.user import User
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_persona_repository import ChatPersonaRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.persona_repository import PersonaRepository
from app.services.exceptions import (
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


@dataclass
class ThinkingTurnEvent:
    """ペルソナが選ばれ、応答を生成中であることを示すイベント。"""

    persona: Persona


@dataclass
class MessageTurnEvent:
    """ペルソナの応答が完成し、保存済みであることを示すイベント。"""

    message: ChatMessage


@dataclass
class TitleTurnEvent:
    """チャットタイトルが自動生成・更新されたことを示すイベント。"""

    title: str


TurnEvent = ThinkingTurnEvent | MessageTurnEvent | TitleTurnEvent
"""`ChatService.stream_turns`が発行するイベント。SSEイベントへの変換はルーター側で行う。"""


class ChatService:
    """t_chat・t_chat_persona・t_chat_messageに対するユースケースを提供する。"""

    def __init__(
        self,
        chat_repository: ChatRepository,
        chat_persona_repository: ChatPersonaRepository,
        chat_message_repository: ChatMessageRepository,
        persona_repository: PersonaRepository,
        chat_graph: ChatGraph,
    ) -> None:
        self._chat_repository = chat_repository
        self._chat_persona_repository = chat_persona_repository
        self._chat_message_repository = chat_message_repository
        self._persona_repository = persona_repository
        self._chat_graph = chat_graph

    async def resolve_internal_id(self, public_id: uuid.UUID) -> int:
        """外部公開用のchat_id（UUID）から内部PK（BIGINT）を解決する。

        所有者チェックはここでは行わない。既存の各メソッドが内部PKに対して
        `_get_owned_chat`で改めて所有者チェックを行うため、ここでは
        「存在するか（論理削除されていないか）」のみを確認する。

        Args:
            public_id: URL・APIレスポンスで公開しているチャットID。

        Returns:
            内部PK（`t_chat.id`）。

        Raises:
            NotFoundError: 該当するチャットが存在しない、または論理削除済みの場合。
        """
        chat = await self._chat_repository.get_by_public_id(public_id)
        if chat is None:
            raise NotFoundError("チャットが見つかりません")
        return chat.id

    async def get_by_user(self, current_user: User) -> Sequence[Chat]:
        """ログインユーザのチャット一覧をupdated_at降順で取得する。

        Args:
            current_user: 操作を行うログインユーザ。

        Returns:
            updated_at降順のチャット一覧。
        """
        return await self._chat_repository.get_by_user(current_user.id)

    async def create(
        self,
        current_user: User,
        persona_ids: Sequence[int],
        chat_mode: ChatMode,
        topic: str | None,
    ) -> Chat:
        """新規チャットを作成する。

        選択可能なペルソナ数の範囲チェック（2〜4体）、および`chat_mode`と`topic`の
        組み合わせの妥当性はAPI層のスキーマバリデーション（CreateChatRequest）で
        実施済みであることを前提とし、ここでは各persona_idの存在確認のみ行う。

        Args:
            current_user: 操作を行うログインユーザ。
            persona_ids: 参加させるペルソナidの並び（この順序がsort_noになる）。
            chat_mode: チャットモード。
            topic: 会話のお題（PERSONA_ONLYのみ。USER_PARTICIPATEDではNone）。

        Returns:
            作成されたチャット。

        Raises:
            NotFoundError: persona_idsに存在しない、または論理削除済みのペルソナが含まれる場合。
        """
        personas = []
        for persona_id in persona_ids:
            persona = await self._persona_repository.get_by_id(persona_id)
            if persona is None:
                raise NotFoundError(f"ペルソナ（id={persona_id}）が見つかりません")
            personas.append(persona)

        chat = Chat(
            user_id=current_user.id,
            title=DEFAULT_CHAT_TITLE,
            chat_mode=chat_mode,
            topic=topic,
            is_stopped=False,
            created_by=current_user.login_id,
            updated_by=current_user.login_id,
        )
        chat = await self._chat_repository.add(chat)

        chat_personas = [
            ChatPersona(
                chat_id=chat.id,
                persona_id=persona_id,
                sort_no=sort_no,
                created_by=current_user.login_id,
                updated_by=current_user.login_id,
            )
            for sort_no, persona_id in enumerate(persona_ids, start=1)
        ]
        await self._chat_persona_repository.add_all(chat_personas)

        created_chat = await self._chat_repository.get_by_id(chat.id)
        if created_chat is None:
            # 直前にflush済みのchatが直後に取得できないことは通常想定しない
            raise NotFoundError("チャットの作成に失敗しました")
        return created_chat

    async def delete(self, chat_id: int, current_user: User) -> None:
        """チャットを論理削除する。

        Args:
            chat_id: 削除対象のチャットid。
            current_user: 操作を行うログインユーザ。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        chat.is_deleted = True
        chat.updated_by = current_user.login_id
        await self._chat_repository.flush()

    async def get_by_id(self, chat_id: int, current_user: User) -> Chat:
        """チャット単体を取得する（S03ヘッダー表示用：タイトル・chat_mode・参加者）。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。

        Returns:
            該当チャット。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        return await self._get_owned_chat(chat_id, current_user)

    async def get_chat_mode(self, chat_id: int, current_user: User) -> ChatMode:
        """チャットのモードのみを取得する（ターン上限決定・SSE配信時のループ継続要否判定用）。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。

        Returns:
            chat_mode。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        return chat.chat_mode

    async def get_messages(
        self, chat_id: int, current_user: User
    ) -> Sequence[ChatMessage]:
        """チャットのメッセージ一覧をsort_no順で取得する。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。

        Returns:
            sort_no昇順のメッセージ一覧。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        await self._get_owned_chat(chat_id, current_user)
        return await self._chat_message_repository.get_by_chat(chat_id)

    async def stop(self, chat_id: int, current_user: User) -> None:
        """自動進行中・連鎖発言中の会話を中断する。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うユーザ。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        chat.is_stopped = True
        chat.updated_by = current_user.login_id
        await self._chat_repository.flush()

    async def save_user_message(
        self, chat_id: int, current_user: User, user_message: str | None
    ) -> ChatMessage:
        """USER_PARTICIPATEDモードでのユーザー発言を保存する。

        LLM呼び出しを伴わないため、StreamingResponse開始前に実行し、
        例外を通常のHTTPエラーレスポンス（404/403/400）として返せるようにする。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。
            user_message: ユーザー発言本文。

        Returns:
            保存されたメッセージ。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
            ValidationError: user_messageが空の場合。
        """
        await self._get_owned_chat(chat_id, current_user)
        if not user_message:
            raise ValidationError("USER_PARTICIPATEDモードではuser_messageが必須です")
        sort_no = await self._chat_message_repository.get_next_sort_no(chat_id)
        user_chat_message = ChatMessage(
            chat_id=chat_id,
            persona_id=None,
            sort_no=sort_no,
            speaker_type=SpeakerType.USER,
            message=user_message,
            created_by=current_user.login_id,
            updated_by=current_user.login_id,
        )
        return await self._chat_message_repository.add(user_chat_message)

    async def stream_turns(
        self,
        chat_id: int,
        current_user: User,
        chat_mode: ChatMode,
        request: Request,
    ) -> AsyncIterator[TurnEvent]:
        """LLMグラフ（app/llm/）を実行し、ターン（話者選択→応答生成→タイトル更新）の
        進行に応じてイベントを逐次発行する。

        PERSONA_ONLYの自動進行・USER_PARTICIPATEDの連鎖発言は、同じグラフ構造を
        1回の実行内でのループとして表現しているため、本メソッドの呼び出しは
        1リクエストにつき1回のみでよい。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。
            chat_mode: チャットモード（ターン上限の決定に使う）。
            request: クライアント切断検知用。

        Yields:
            ペルソナ選択・応答生成・タイトル更新の各イベント。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
            ExternalServiceError: LLM呼び出しがリトライを使い切っても失敗した場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        participants = [chat_persona.persona for chat_persona in chat.chat_personas]
        persona_by_id = {persona.id: persona for persona in participants}
        history = await self._chat_message_repository.get_by_chat(chat_id)

        max_turns = (
            constants.PERSONA_ONLY_MAX_TURNS_PER_REQUEST
            if chat_mode == ChatMode.PERSONA_ONLY
            else constants.USER_PARTICIPATED_CHAIN_MAX_TURNS
        )
        initial_state: ChatTurnState = {
            "chat_mode": chat_mode,
            "topic": chat.topic,
            "participants": [persona_profile_from_model(p) for p in participants],
            "history": [turn_entry_from_message(m) for m in history],
            "should_generate_title": chat.title == DEFAULT_CHAT_TITLE,
            "turn_count": 0,
            "replies_this_turn": 0,
            "current_persona_id": None,
            "generated_reply_text": None,
            "generated_title": None,
        }
        run_context = ChatRunContext(
            request=request,
            max_turns=max_turns,
            is_stopped=lambda: self._chat_repository.get_is_stopped(chat_id),
        )

        current_persona: Persona | None = None
        try:
            async for chunk in self._chat_graph.astream(
                initial_state, context=run_context, stream_mode="updates"
            ):
                for node_name, delta in chunk.items():
                    if not delta:
                        continue
                    if node_name == "select_speaker":
                        persona_id = delta.get("current_persona_id")
                        if persona_id is not None:
                            current_persona = persona_by_id[persona_id]
                            yield ThinkingTurnEvent(persona=current_persona)
                    elif node_name == "generate_reply":
                        if current_persona is None:
                            raise RuntimeError(
                                "current_personaが未設定のままgenerate_replyの"
                                "結果を受信しました"
                            )
                        yield MessageTurnEvent(
                            message=await self._record_persona_reply(
                                chat_id, current_user, current_persona, delta
                            )
                        )
                    elif node_name == "maybe_update_title":
                        title = delta.get("generated_title")
                        if title:
                            chat.title = title
                            chat.updated_by = current_user.login_id
                            await self._chat_repository.flush()
                            yield TitleTurnEvent(title=title)
        except Exception as exc:
            if not is_llm_api_error(exc):
                raise
            raise ExternalServiceError("応答の生成に失敗しました") from exc

    async def _record_persona_reply(
        self,
        chat_id: int,
        current_user: User,
        persona: Persona,
        delta: dict[str, object],
    ) -> ChatMessage:
        """generate_replyノードの出力をChatMessageとして永続化する。"""
        text = delta["generated_reply_text"]
        assert isinstance(text, str)
        sort_no = await self._chat_message_repository.get_next_sort_no(chat_id)
        chat_message = ChatMessage(
            chat_id=chat_id,
            persona_id=persona.id,
            sort_no=sort_no,
            speaker_type=SpeakerType.PERSONA,
            message=text,
            created_by=current_user.login_id,
            updated_by=current_user.login_id,
        )
        return await self._chat_message_repository.add(chat_message)

    async def _get_owned_chat(self, chat_id: int, current_user: User) -> Chat:
        """チャットの存在確認と所有者チェックをまとめて行う。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。

        Returns:
            該当チャット。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: ログインユーザ以外が作成したチャットの場合。
        """
        chat = await self._chat_repository.get_by_id(chat_id)
        if chat is None:
            raise NotFoundError("チャットが見つかりません")
        if chat.user_id != current_user.id:
            raise ForbiddenError("このチャットを操作する権限がありません")
        return chat

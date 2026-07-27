"""チャット・チャットメッセージに関するユースケース。"""

from collections.abc import Sequence

from app.config.constants import DEFAULT_CHAT_TITLE
from app.models.chat import Chat, ChatMode
from app.models.chat_message import ChatMessage, SpeakerType
from app.models.chat_persona import ChatPersona
from app.models.persona import Persona
from app.models.user import User
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_persona_repository import ChatPersonaRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.persona_repository import PersonaRepository
from app.services.exceptions import ForbiddenError, NotFoundError, ValidationError


def _mock_persona_reply(persona: Persona) -> str:
    """ペルソナの応答を仮の固定文言で生成する。

    app/llm/未実装のための暫定処理。実際のLLM連携実装時にこの関数を置き換える。
    """
    return f"（モック応答）{persona.name}として応答する予定の内容です。"


class ChatService:
    """t_chat・t_chat_persona・t_chat_messageに対するユースケースを提供する。"""

    def __init__(
        self,
        chat_repository: ChatRepository,
        chat_persona_repository: ChatPersonaRepository,
        chat_message_repository: ChatMessageRepository,
        persona_repository: PersonaRepository,
    ) -> None:
        self._chat_repository = chat_repository
        self._chat_persona_repository = chat_persona_repository
        self._chat_message_repository = chat_message_repository
        self._persona_repository = persona_repository

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
    ) -> Chat:
        """新規チャットを作成する。

        選択可能なペルソナ数の範囲チェック（2〜4体）はAPI層のスキーマバリデーションで
        実施済みであることを前提とし、ここでは各persona_idの存在確認のみ行う。

        Args:
            current_user: 操作を行うログインユーザ。
            persona_ids: 参加させるペルソナidの並び（この順序がsort_noになる）。
            chat_mode: チャットモード。

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

    async def get_chat_mode(self, chat_id: int, current_user: User) -> ChatMode:
        """チャットのモードのみを取得する（SSE配信時のループ継続要否判定用）。

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

    async def get_is_stopped(self, chat_id: int) -> bool:
        """会話停止フラグの最新値を取得する（PERSONA_ONLYの自動進行ポーリング用）。

        Args:
            chat_id: 対象のチャットid。

        Returns:
            is_stoppedの最新値。
        """
        return await self._chat_repository.get_is_stopped(chat_id)

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
            current_user: 操作を行うログインユーザ。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        chat.is_stopped = True
        chat.updated_by = current_user.login_id
        await self._chat_repository.flush()

    async def advance_conversation(
        self,
        chat_id: int,
        current_user: User,
        user_message: str | None,
    ) -> Sequence[ChatMessage]:
        """会話を1ターン進める（暫定：ペルソナ応答は固定文言のモック）。

        app/llm/未実装のため、実際のLLM呼び出し・「会話を続けるべきか」の判断による
        連鎖発言・PERSONA_ONLYモードの自動継続ループは、この時点では行わない
        （1ターンにつきペルソナ応答は常に1件のみ生成する）。

        Args:
            chat_id: 対象のチャットid。
            current_user: 操作を行うログインユーザ。
            user_message: USER_PARTICIPATEDモードでのユーザー発言本文。PERSONA_ONLYモードではNone。

        Returns:
            今回のターンで新規作成されたメッセージ一覧（sort_no昇順）。

        Raises:
            NotFoundError: チャットが存在しない、または論理削除済みの場合。
            ForbiddenError: 他ユーザーが作成したチャットの場合。
            ValidationError: USER_PARTICIPATEDモードでuser_messageが空の場合。
        """
        chat = await self._get_owned_chat(chat_id, current_user)
        created_messages: list[ChatMessage] = []

        if chat.chat_mode == ChatMode.USER_PARTICIPATED:
            if not user_message:
                raise ValidationError(
                    "USER_PARTICIPATEDモードではuser_messageが必須です"
                )
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
            created_messages.append(
                await self._chat_message_repository.add(user_chat_message)
            )

        persona = self._pick_next_persona(chat)
        sort_no = await self._chat_message_repository.get_next_sort_no(chat_id)
        persona_chat_message = ChatMessage(
            chat_id=chat_id,
            persona_id=persona.id,
            sort_no=sort_no,
            speaker_type=SpeakerType.PERSONA,
            message=_mock_persona_reply(persona),
            created_by=current_user.login_id,
            updated_by=current_user.login_id,
        )
        created_messages.append(
            await self._chat_message_repository.add(persona_chat_message)
        )
        return created_messages

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

    def _pick_next_persona(self, chat: Chat) -> Persona:
        """次に発言するペルソナを選ぶ（暫定：先頭の参加者を固定的に選択するモック）。

        Args:
            chat: chat_personas（sort_no順）がロード済みのチャット。

        Returns:
            発言するペルソナ。

        Raises:
            NotFoundError: チャットに参加しているペルソナが1件もない場合。
        """
        if not chat.chat_personas:
            raise NotFoundError("チャットに参加しているペルソナが見つかりません")
        return chat.chat_personas[0].persona

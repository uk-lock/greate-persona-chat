"""チャット（t_chat）のリポジトリ。"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.chat import Chat
from app.models.chat_persona import ChatPersona
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """t_chatに対するCRUD操作を提供する。"""

    model = Chat

    async def get_by_id(self, entity_id: int) -> Chat | None:
        """チャットを、参加者組み立てに必要なchat_persona・personaごと取得する。

        Args:
            entity_id: チャットid。

        Returns:
            該当チャット。存在しない、または論理削除済みの場合はNone。
        """
        stmt = (
            select(Chat)
            .where(Chat.id == entity_id, Chat.is_deleted.is_(False))
            .options(selectinload(Chat.chat_personas).selectinload(ChatPersona.persona))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: uuid.UUID) -> Chat | None:
        """外部公開用ID（UUID）からチャットを取得する（内部PKの解決用）。

        Args:
            public_id: URL・APIレスポンスで公開しているチャットID。

        Returns:
            該当チャット。存在しない、または論理削除済みの場合はNone。
        """
        stmt = select(Chat).where(
            Chat.public_id == public_id, Chat.is_deleted.is_(False)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> Sequence[Chat]:
        """ログインユーザのチャット一覧をupdated_at降順で取得する。

        Args:
            user_id: ユーザid。

        Returns:
            updated_at降順のチャット一覧。
        """
        stmt = (
            select(Chat)
            .where(Chat.user_id == user_id, Chat.is_deleted.is_(False))
            .options(selectinload(Chat.chat_personas).selectinload(ChatPersona.persona))
            .order_by(Chat.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_is_stopped(self, chat_id: int) -> bool:
        """会話停止フラグの最新値のみを取得する。

        Chatエンティティをこのセッション内で既に取得済みの場合、SQLAlchemyの
        identity mapにより`get_by_id`を呼び直しても他コネクションでの更新
        （例：別リクエストからの`POST /chats/{chat_id}/stop`）が反映されないことがある。
        本メソッドはカラム単体のSELECTのため、その影響を受けず常に最新値を返す。

        Args:
            chat_id: チャットid。

        Returns:
            is_stoppedの最新値。
        """
        stmt = select(Chat.is_stopped).where(Chat.id == chat_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

"""チャットメッセージ（t_chat_message）のリポジトリ。"""

from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.chat_message import ChatMessage
from app.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """t_chat_messageに対するCRUD操作を提供する。"""

    model = ChatMessage

    async def get_by_chat(self, chat_id: int) -> Sequence[ChatMessage]:
        """指定チャットのメッセージ一覧をsort_no順で取得する。

        Args:
            chat_id: チャットid。

        Returns:
            sort_no昇順のメッセージ一覧。
        """
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id, ChatMessage.is_deleted.is_(False))
            .order_by(ChatMessage.sort_no)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_next_sort_no(self, chat_id: int) -> int:
        """指定チャットにおける次のsort_noを算出する。

        Args:
            chat_id: チャットid。

        Returns:
            現在の最大sort_no + 1（メッセージが存在しない場合は1）。
        """
        stmt = select(func.max(ChatMessage.sort_no)).where(
            ChatMessage.chat_id == chat_id
        )
        result = await self._session.execute(stmt)
        max_sort_no = result.scalar_one()
        return (max_sort_no or 0) + 1

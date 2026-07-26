"""ユーザ（m_user）のリポジトリ。"""

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """m_userに対するCRUD操作を提供する。"""

    model = User

    async def get_by_login_id(self, login_id: str) -> User | None:
        """login_idでユーザを取得する（論理削除済みは対象外）。

        Args:
            login_id: ログインID。

        Returns:
            該当ユーザ。存在しない場合はNone。
        """
        stmt = select(User).where(User.login_id == login_id, User.is_deleted.is_(False))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

"""ペルソナ（m_persona）のリポジトリ。"""

from collections.abc import Sequence

from sqlalchemy import select

from app.models.persona import Persona
from app.repositories.base import BaseRepository


class PersonaRepository(BaseRepository[Persona]):
    """m_personaに対するCRUD操作を提供する。"""

    model = Persona

    async def get_all(self) -> Sequence[Persona]:
        """論理削除されていない全ペルソナをid昇順で取得する。

        Returns:
            id昇順のペルソナ一覧。
        """
        stmt = select(Persona).where(Persona.is_deleted.is_(False)).order_by(Persona.id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Persona | None:
        """名前が一致する未削除のペルソナを取得する。

        `name`にDB上の一意制約はないため、あくまで簡易的な重複チェック用途
        （`tools/insert_init_data.py`のべき等性確保）に使う。

        Args:
            name: ペルソナ名。

        Returns:
            該当ペルソナ。存在しない場合はNone。
        """
        stmt = select(Persona).where(
            Persona.name == name, Persona.is_deleted.is_(False)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

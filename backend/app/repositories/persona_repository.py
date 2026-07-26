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

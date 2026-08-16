"""ペルソナ情報の参照に関するユースケース。"""

from collections.abc import Sequence

from app.models.persona import Persona
from app.repositories.persona_repository import PersonaRepository
from app.services.exceptions import NotFoundError


class PersonaService:
    """m_personaの参照系ユースケースを提供する。"""

    def __init__(self, persona_repository: PersonaRepository) -> None:
        self._persona_repository = persona_repository

    async def get_all(self) -> Sequence[Persona]:
        """論理削除されていない全ペルソナをid昇順で取得する。

        Returns:
            id昇順のペルソナ一覧。
        """
        return await self._persona_repository.get_all()

    async def get_by_id(self, persona_id: int) -> Persona:
        """ペルソナ詳細を取得する。

        Args:
            persona_id: 取得対象のペルソナid。

        Returns:
            該当ペルソナ。

        Raises:
            NotFoundError: 対象が存在しない、または論理削除済みの場合。
        """
        persona = await self._persona_repository.get_by_id(persona_id)
        if persona is None:
            raise NotFoundError("ペルソナが見つかりません")
        return persona

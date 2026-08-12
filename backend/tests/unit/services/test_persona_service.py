"""PersonaService（ペルソナ参照）の単体テスト。

PersonaRepositoryはAsyncMockに置き換え、実DBには一切依存しない。
"""

from unittest.mock import AsyncMock

import pytest

from app.repositories.persona_repository import PersonaRepository
from app.services.exceptions import NotFoundError
from app.services.persona_service import PersonaService
from tests.factories import make_persona


@pytest.fixture
def persona_repository() -> AsyncMock:
    return AsyncMock(spec=PersonaRepository)


@pytest.fixture
def persona_service(persona_repository: AsyncMock) -> PersonaService:
    return PersonaService(persona_repository)


class TestGetAll:
    async def test_get_all_returns_personas_from_repository(
        self, persona_service: PersonaService, persona_repository: AsyncMock
    ) -> None:
        personas = [make_persona(id=1), make_persona(id=2, name="プラトン")]
        persona_repository.get_all.return_value = personas

        result = await persona_service.get_all()

        assert result == personas

    async def test_get_all_returns_empty_list_when_no_persona(
        self, persona_service: PersonaService, persona_repository: AsyncMock
    ) -> None:
        persona_repository.get_all.return_value = []

        result = await persona_service.get_all()

        assert result == []


class TestGetById:
    async def test_get_by_id_returns_persona_when_found(
        self, persona_service: PersonaService, persona_repository: AsyncMock
    ) -> None:
        persona = make_persona(id=5)
        persona_repository.get_by_id.return_value = persona

        result = await persona_service.get_by_id(5)

        assert result is persona

    async def test_get_by_id_raises_not_found_when_missing(
        self, persona_service: PersonaService, persona_repository: AsyncMock
    ) -> None:
        persona_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await persona_service.get_by_id(999)

"""ペルソナ関連のルーター。"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_persona_service
from app.api.schemas.persona import PersonaDetailResponse, PersonaSummaryResponse
from app.models.user import User
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("")
async def get_personas(
    current_user: User = Depends(get_current_user),
    persona_service: PersonaService = Depends(get_persona_service),
) -> list[PersonaSummaryResponse]:
    """ペルソナ一覧をid昇順で取得する。"""
    personas = await persona_service.get_all()
    return [PersonaSummaryResponse.model_validate(persona) for persona in personas]


@router.get("/{persona_id}")
async def get_persona(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    persona_service: PersonaService = Depends(get_persona_service),
) -> PersonaDetailResponse:
    """ペルソナ詳細を取得する。

    Raises:
        NotFoundError: 対象が存在しない、または論理削除済みの場合（404に変換される）。
    """
    persona = await persona_service.get_by_id(persona_id)
    return PersonaDetailResponse.model_validate(persona)

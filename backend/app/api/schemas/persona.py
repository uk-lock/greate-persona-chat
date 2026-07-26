"""ペルソナ関連のレスポンススキーマ。"""

from pydantic import BaseModel


class PersonaSummaryResponse(BaseModel):
    """ペルソナ一覧（GET /personas）の1要素。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    image_url: str | None
    summary: str | None


class PersonaDetailResponse(BaseModel):
    """ペルソナ詳細（GET /personas/{persona_id}）。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    image_url: str | None
    country: str | None
    era: str | None
    summary: str | None
    description: str | None
    personality: str | None
    biography: str | None
    sample_quotes: list[str] | None

"""ペルソナ関連のレスポンススキーマ。"""

from typing import TypedDict

from pydantic import BaseModel


class BiographyEntryResponse(TypedDict):
    """biographyの年表1件分（例：`{"year": 1780, "event": "XXXをした"}`）。"""

    year: int
    event: str


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
    biography: list[BiographyEntryResponse] | None
    sample_quotes: list[str] | None

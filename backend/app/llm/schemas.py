"""構造化出力（`with_structured_output`）用のPydanticスキーマ。"""

from pydantic import BaseModel, Field


class SpeakerSelection(BaseModel):
    """応答ペルソナ選択の結果。"""

    persona_id: int | None = Field(
        description=(
            "次に応答するペルソナのpersona_id。"
            "これ以上ペルソナが発言する必要がない（会話を終えてユーザーに"
            "制御を戻すべき）と判断した場合のみnullを指定する。"
        )
    )


class TitleGeneration(BaseModel):
    """チャットタイトル自動生成の結果。"""

    title: str = Field(description="会話内容を要約した短い日本語のチャットタイトル。")

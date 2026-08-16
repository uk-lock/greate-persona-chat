"""LangGraphの状態（ChatTurnState）と、DBモデルからの変換ヘルパー。"""

from typing import Literal, TypedDict

from app.models.chat import ChatMode
from app.models.chat_message import ChatMessage, SpeakerType
from app.models.persona import BiographyEntry, Persona


class PersonaProfile(TypedDict):
    """話者選択・応答生成のプロンプトに渡すペルソナの最小情報。"""

    persona_id: int
    name: str
    personality: str | None
    conversation_policy: str | None
    description: str | None
    summary: str | None
    biography: str | None
    sample_quotes: str | None


class TurnEntry(TypedDict):
    """会話履歴1件分（グラフ内でのプロンプト構築専用の軽量表現）。"""

    speaker: Literal["USER", "PERSONA"]
    persona_id: int | None
    text: str


class ChatTurnState(TypedDict):
    """チャットの1リクエスト（`stream_turns`の1回の呼び出し）分のグラフ状態。"""

    chat_mode: ChatMode
    topic: str | None
    participants: list[PersonaProfile]
    history: list[TurnEntry]
    should_generate_title: bool
    turn_count: int
    replies_this_turn: int
    current_persona_id: int | None
    generated_reply_text: str | None
    generated_title: str | None


def persona_profile_from_model(persona: Persona) -> PersonaProfile:
    """PersonaモデルからLLMプロンプト用の軽量表現を組み立てる。"""
    return PersonaProfile(
        persona_id=persona.id,
        name=persona.name,
        personality=persona.personality,
        conversation_policy=persona.conversation_policy,
        description=persona.description,
        summary=persona.summary,
        biography=_format_biography(persona.biography),
        sample_quotes=_format_sample_quotes(persona.sample_quotes),
    )


def turn_entry_from_message(message: ChatMessage) -> TurnEntry:
    """ChatMessageからグラフ内履歴表現を組み立てる。"""
    return TurnEntry(
        speaker="USER" if message.speaker_type == SpeakerType.USER else "PERSONA",
        persona_id=message.persona_id,
        text=message.message,
    )


def _format_biography(biography: list[BiographyEntry] | None) -> str | None:
    if not biography:
        return None
    return "\n".join(f"{entry['year']}年: {entry['event']}" for entry in biography)


def _format_sample_quotes(quotes: list[str] | None) -> str | None:
    if not quotes:
        return None
    return "\n".join(f"「{quote}」" for quote in quotes)

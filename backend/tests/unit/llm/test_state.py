"""`app/llm/state.py`の単体テスト。

DBモデル（Persona・ChatMessage）からLLMグラフ用の軽量表現への変換ロジックを検証する。
"""

from app.llm.state import persona_profile_from_model, turn_entry_from_message
from app.models.chat_message import SpeakerType
from tests.factories import make_chat_message, make_persona


class TestPersonaProfileFromModel:
    def test_converts_all_fields(self) -> None:
        persona = make_persona(
            id=1,
            name="ソクラテス",
            personality="謙虚",
            conversation_policy="対話を通じて真理を探究する",
            description="古代ギリシャの哲学者",
            summary="無知の知で知られる",
            biography=[{"year": -469, "event": "アテナイに生まれる"}],
            sample_quotes=["無知の知"],
        )

        profile = persona_profile_from_model(persona)

        assert profile["persona_id"] == 1
        assert profile["name"] == "ソクラテス"
        assert profile["biography"] == "-469年: アテナイに生まれる"
        assert profile["sample_quotes"] == "「無知の知」"

    def test_none_biography_and_quotes_are_none(self) -> None:
        persona = make_persona(biography=None, sample_quotes=None)

        profile = persona_profile_from_model(persona)

        assert profile["biography"] is None
        assert profile["sample_quotes"] is None

    def test_empty_biography_and_quotes_are_none(self) -> None:
        """境界値：空配列も`None`と同様に扱う（空文字ではない）。"""
        persona = make_persona(biography=[], sample_quotes=[])

        profile = persona_profile_from_model(persona)

        assert profile["biography"] is None
        assert profile["sample_quotes"] is None

    def test_multiple_biography_entries_and_quotes_are_joined(self) -> None:
        persona = make_persona(
            biography=[
                {"year": 1, "event": "誕生"},
                {"year": 2, "event": "旅立ち"},
            ],
            sample_quotes=["名言1", "名言2"],
        )

        profile = persona_profile_from_model(persona)

        assert profile["biography"] == "1年: 誕生\n2年: 旅立ち"
        assert profile["sample_quotes"] == "「名言1」\n「名言2」"


class TestTurnEntryFromMessage:
    def test_user_message(self) -> None:
        message = make_chat_message(
            speaker_type=SpeakerType.USER, persona_id=None, message="こんにちは"
        )

        entry = turn_entry_from_message(message)

        assert entry == {"speaker": "USER", "persona_id": None, "text": "こんにちは"}

    def test_persona_message(self) -> None:
        message = make_chat_message(
            speaker_type=SpeakerType.PERSONA, persona_id=5, message="やあ"
        )

        entry = turn_entry_from_message(message)

        assert entry == {"speaker": "PERSONA", "persona_id": 5, "text": "やあ"}

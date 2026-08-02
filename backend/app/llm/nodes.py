"""LangGraphのノード関数（LLM呼び出し本体）。

`app/llm/`はLLM I/Oに専念し、DBアクセスは行わない
（永続化はChatService側で行う。backend-python.md 8節のレイヤー方針）。
各ノードは対応するチャットモデルをクロージャとして受け取るファクトリ関数として
定義し、`graph.py`側でDI（本物のモデル or テスト用スタブ）を差し込めるようにする。
"""

from collections.abc import Awaitable, Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Command

from app.config.constants import LLM_HISTORY_MAX_MESSAGES
from app.llm.context import ChatRunContext
from app.llm.schemas import SpeakerSelection, TitleGeneration
from app.llm.state import ChatTurnState, PersonaProfile, TurnEntry
from app.models.chat import ChatMode

Node = Callable[..., Awaitable[Command]]


async def check_can_continue(
    state: ChatTurnState, *, runtime: Runtime[ChatRunContext]
) -> Command:
    """安全弁チェック（切断・停止・ターン数上限）。継続不可なら即座にグラフを終了する。"""
    if state["turn_count"] >= runtime.context.max_turns:
        return Command(goto=END)
    if await runtime.context.request.is_disconnected():
        return Command(goto=END)
    if await runtime.context.is_stopped():
        return Command(goto=END)
    return Command(goto="select_speaker")


def make_select_speaker(model: BaseChatModel) -> Node:
    """次に発言するペルソナを選ぶノードを構築する。

    PERSONA_ONLYでは常にいずれかのペルソナを選ぶ（停止の選択肢を与えない）。
    USER_PARTICIPATEDでは、まだこのターンでペルソナ応答が無い間は必ずペルソナを
    選ばせ（ユーザー発言には最低1回応答する）、1件以上生成済みなら停止
    （`persona_id=None`）を選べるようにする＝これが連鎖発言の継続判断を兼ねる。
    """
    structured_model = model.with_structured_output(SpeakerSelection)

    async def select_speaker(
        state: ChatTurnState, *, runtime: Runtime[ChatRunContext]
    ) -> Command:
        can_stop = (
            state["chat_mode"] == ChatMode.USER_PARTICIPATED
            and state["replies_this_turn"] > 0
        )
        candidates = "\n".join(
            f"- persona_id={participant['persona_id']} | name={participant['name']} | conversation_policy={participant['conversation_policy']}"
            for participant in state["participants"]
        )
        stop_instruction = (
            "これ以上ペルソナが発言する必要がないと判断した場合は、"
            "persona_idにnullを指定してください。"
            if can_stop
            else "必ずいずれかのpersona_idを指定してください（nullは選べません）。"
        )
        system = SystemMessage(
            content=(
                "あなたは複数の偉人ペルソナが参加するチャットの進行役です。"
                "これまでの会話の流れおよび、各ペルソナの特徴を踏まえ、次に発言するのにふさわしいペルソナを"
                f"1人選んでください。\n候補:\n{candidates}\n{stop_instruction}"
                f"{_topic_instruction(state['topic'])}"
            )
        )
        transcript = HumanMessage(
            content=_render_transcript(state["history"], state["participants"])
        )
        result = await structured_model.ainvoke([system, transcript])
        assert isinstance(result, SpeakerSelection)
        persona_id = result.persona_id
        if not can_stop and persona_id is None:
            persona_id = state["participants"][0]["persona_id"]
        if persona_id is None:
            return Command(update={"current_persona_id": None}, goto=END)
        return Command(update={"current_persona_id": persona_id}, goto="generate_reply")

    return select_speaker


def make_generate_reply(model: BaseChatModel) -> Node:
    """選ばれたペルソナの応答本文を生成するノードを構築する。"""

    async def generate_reply(
        state: ChatTurnState, *, runtime: Runtime[ChatRunContext]
    ) -> Command:
        persona_id = state["current_persona_id"]
        if persona_id is None:
            # select_speakerがNoneを選んだ場合はENDへ遷移済みのため到達しない。
            raise RuntimeError(
                "current_persona_idが未設定のままgenerate_replyに到達しました"
            )
        persona = next(
            participant
            for participant in state["participants"]
            if participant["persona_id"] == persona_id
        )
        system = SystemMessage(
            content=(
                f"あなたは偉人ペルソナ「{persona['name']}」として、ユーザーや他の"
                "参加者と会話しています。以下のプロフィールになりきり、一人称で"
                "自然に応答してください。地の文・状況説明・他の参加者の発言は含めず、"
                f"あなた自身のセリフのみを返してください。\n\n{_persona_profile_text(persona)}"
                f"{_topic_instruction(state['topic'])}"
            )
        )
        messages: list[BaseMessage] = [system]
        for entry in state["history"][-LLM_HISTORY_MAX_MESSAGES:]:
            if entry["speaker"] == "PERSONA" and entry["persona_id"] == persona_id:
                messages.append(AIMessage(content=entry["text"]))
            else:
                speaker = _speaker_label(entry, state["participants"])
                messages.append(HumanMessage(content=f"{speaker}: {entry['text']}"))
        response = await model.ainvoke(messages)
        text = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        new_entry: TurnEntry = {
            "speaker": "PERSONA",
            "persona_id": persona_id,
            "text": text,
        }
        return Command(
            update={
                "generated_reply_text": text,
                "history": [*state["history"], new_entry],
                "replies_this_turn": state["replies_this_turn"] + 1,
                "turn_count": state["turn_count"] + 1,
            },
            goto="maybe_update_title",
        )

    return generate_reply


def make_maybe_update_title(model: BaseChatModel) -> Node:
    """チャットタイトルを自動生成するノードを構築する（最初の1回のみ実行される）。"""
    structured_model = model.with_structured_output(TitleGeneration)

    async def maybe_update_title(
        state: ChatTurnState, *, runtime: Runtime[ChatRunContext]
    ) -> Command:
        if not state["should_generate_title"]:
            return Command(goto="check_can_continue")
        system = SystemMessage(
            content=(
                "以下の会話内容を踏まえ、このチャットにふさわしい短い日本語の"
                "タイトルを1つ生成してください。20文字程度を目安にしてください。"
            )
        )
        transcript = HumanMessage(
            content=_render_transcript(state["history"], state["participants"])
        )
        result = await structured_model.ainvoke([system, transcript])
        assert isinstance(result, TitleGeneration)
        return Command(
            update={"generated_title": result.title, "should_generate_title": False},
            goto="check_can_continue",
        )

    return maybe_update_title


def _topic_instruction(topic: str | None) -> str:
    """PERSONA_ONLYの会話のお題をsystem promptへ差し込む文言を組み立てる。

    履歴（`LLM_HISTORY_MAX_MESSAGES`件まで）が流れて古い発言が見えなくなっても
    方向性を保てるよう、履歴ではなくsystem prompt側に毎ターン含める。
    """
    if not topic:
        return ""
    return f"\n\nこの会話のお題は「{topic}」です。お題に沿った発言を心がけてください。"


def _persona_name(participants: list[PersonaProfile], persona_id: int | None) -> str:
    if persona_id is None:
        return "不明な参加者"
    for participant in participants:
        if participant["persona_id"] == persona_id:
            return participant["name"]
    return "不明な参加者"


def _speaker_label(entry: TurnEntry, participants: list[PersonaProfile]) -> str:
    if entry["speaker"] == "USER":
        return "ユーザー"
    return _persona_name(participants, entry["persona_id"])


def _render_transcript(
    history: list[TurnEntry], participants: list[PersonaProfile]
) -> str:
    recent = history[-LLM_HISTORY_MAX_MESSAGES:]
    if not recent:
        return "（まだ発言はありません）"
    return "\n".join(
        f"{_speaker_label(entry, participants)}: {entry['text']}" for entry in recent
    )


def _persona_profile_text(persona: PersonaProfile) -> str:
    fields = [
        f"名前: {persona['name']}",
        f"性格: {persona['personality']}" if persona["personality"] else None,
        f"会話方針: {persona['conversation_policy']}"
        if persona["conversation_policy"]
        else None,
        f"説明: {persona['description']}" if persona["description"] else None,
        f"概要: {persona['summary']}" if persona["summary"] else None,
        f"年表: {persona['biography']}" if persona["biography"] else None,
        f"口癖・発言例: {persona['sample_quotes']}"
        if persona["sample_quotes"]
        else None,
    ]
    return "\n".join(field for field in fields if field is not None)

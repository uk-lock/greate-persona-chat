"""チャットのLLMオーケストレーショングラフの定義・構築。

「（継続判定）→タイトル更新→話者選択→応答生成」という循環を1つの
`StateGraph`として表現する。タイトル更新は最初の1回のみ、ペルソナの応答を
待たずに（ユーザーの最初の発言 or 事前入力されたお題のみを根拠に）行う。
PERSONA_ONLYの自動進行とUSER_PARTICIPATEDの連鎖発言は、同じグラフ構造を
共有し、`chat_mode`による分岐（select_speakerが停止を選べるか、
context.max_turns）だけで挙動を変える。
"""

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.llm.context import ChatRunContext
from app.llm.models import build_reply_model, build_selection_model, build_title_model
from app.llm.nodes import (
    check_can_continue,
    make_generate_reply,
    make_maybe_update_title,
    make_select_speaker,
)
from app.llm.retry import LLM_RETRY_POLICY
from app.llm.state import ChatTurnState

ChatGraph = CompiledStateGraph[
    ChatTurnState, ChatRunContext, ChatTurnState, ChatTurnState
]


def build_chat_graph(
    *,
    reply_model: BaseChatModel | None = None,
    selection_model: BaseChatModel | None = None,
    title_model: BaseChatModel | None = None,
) -> ChatGraph:
    """チャットターン進行グラフを構築・コンパイルする。

    `reply_model`等を明示的に渡すことで、テスト時にスタブへ差し替えられる。
    """
    graph = StateGraph(ChatTurnState, context_schema=ChatRunContext)
    graph.add_node("check_can_continue", check_can_continue)
    graph.add_node(
        "select_speaker",
        make_select_speaker(selection_model or build_selection_model()),
        retry_policy=LLM_RETRY_POLICY,
    )
    graph.add_node(
        "generate_reply",
        make_generate_reply(reply_model or build_reply_model()),
        retry_policy=LLM_RETRY_POLICY,
    )
    graph.add_node(
        "maybe_update_title",
        make_maybe_update_title(title_model or build_title_model()),
        retry_policy=LLM_RETRY_POLICY,
    )
    graph.set_entry_point("check_can_continue")
    return graph.compile()

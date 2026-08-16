"""グラフ実行時にノードへ注入するリクエストスコープの依存（LangGraphのRuntime Context）。

チャットモデル自体（用途別に3種）はリクエストをまたいで共通のため、ここには含めず
`graph.py`がノードのクロージャとして注入する。ここに置くのは、リクエストごとに
異なる値・DBアクセスが必要な値のみとする。
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Request


@dataclass
class ChatRunContext:
    """1回の`ChatService.stream_turns`実行（＝1リクエスト）を通じて共有される依存。"""

    request: Request
    """クライアント切断検知用。"""

    max_turns: int
    """このリクエストで許容するターン数の上限（chat_modeにより呼び出し側が決定する）。"""

    is_stopped: Callable[[], Awaitable[bool]]
    """会話停止フラグ（`t_chat.is_stopped`）の最新値を取得する非同期関数。"""

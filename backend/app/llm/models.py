"""用途別のチャットモデルを構築するモジュール。

`langchain`の`init_chat_model`を使い、`app.config.settings`の各設定値
（`プロバイダ名:モデル名`形式の文字列。例：`openai:gpt-5-mini`）だけで
プロバイダを切り替えられるようにする。呼び出し側（`graph.py`等）は
どのプロバイダを使っているかを意識しない。

リトライはLangGraphの`RetryPolicy`（`retry.py`）に一本化するため、
クライアント自体のリトライは無効化する（`max_retries=0`）。
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config import settings

_PROVIDER_API_KEYS: dict[str, str | None] = {
    "openai": settings.openai_api_key,
    "deepseek": settings.deepseek_api_key,
}
"""プロバイダ名とAPIキーの対応表。利用するプロバイダを追加するたびに拡張する。"""


def _build_model(model: str) -> BaseChatModel:
    provider = model.split(":", 1)[0]
    return init_chat_model(
        model,
        api_key=_PROVIDER_API_KEYS.get(provider),
        max_retries=0,
    )


def build_reply_model() -> BaseChatModel:
    """ペルソナ応答生成用のチャットモデルを構築する。"""
    return _build_model(settings.reply_model)


def build_selection_model() -> BaseChatModel:
    """応答ペルソナ選択（連鎖発言の継続判断を含む）用のチャットモデルを構築する。"""
    return _build_model(settings.selection_model)


def build_title_model() -> BaseChatModel:
    """チャットタイトル自動生成用のチャットモデルを構築する。"""
    return _build_model(settings.title_model)

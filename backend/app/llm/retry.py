"""LLM呼び出し失敗時の再試行可否判定。

backend-python.md 13節「タイムアウト・5xx・429等の一時的なエラーのみ少数回
再試行し、4xxクライアントエラーは再試行しない」をLangGraphの`RetryPolicy`で
実現する（ノード単位のリトライに一本化し、各チャットモデル自体のリトライは
無効化している。`models.py`参照）。

複数のLLMプロバイダ（OpenAI・DeepSeek等、今後も増える想定）を横断で扱うため、
特定プロバイダのSDK例外クラスをimportして判定するのではなく、多くのプロバイダSDK
（Stainlessでコード生成されたopenai・anthropic等）に共通する構造で判定する：
APIStatusError系の例外は必ず`status_code`という整数属性を持ち、タイムアウト・
接続エラーの例外クラス名は`APITimeoutError`・`APIConnectionError`で共通している
（openai・anthropicで実際に確認済み）。

同じ理由（プロバイダ非依存）から、`is_llm_api_error`（LLM呼び出し由来のエラーかの
判定）も本モジュールに置く。`app/services/chat_service.py`が「リトライを使い切って
失敗した」ことを`ExternalServiceError`へ変換する際、`except openai.OpenAIError`の
ように特定プロバイダのSDK例外クラスをimportしてしまうと、models.pyのプロバイダ
非依存の意図が崩れるため。
"""

from langgraph.types import RetryPolicy

_TRANSIENT_EXCEPTION_TYPE_NAMES = frozenset({"APITimeoutError", "APIConnectionError"})


def is_llm_api_error(exc: Exception) -> bool:
    """LLMプロバイダのSDKに由来する（＝呼び出し失敗として扱うべき）例外か判定する。"""
    if isinstance(exc, TimeoutError | ConnectionError):
        return True
    if type(exc).__name__ in _TRANSIENT_EXCEPTION_TYPE_NAMES:
        return True
    return isinstance(getattr(exc, "status_code", None), int)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError | ConnectionError):
        return True
    if type(exc).__name__ in _TRANSIENT_EXCEPTION_TYPE_NAMES:
        return True
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code >= 500 or status_code == 429
    return False


LLM_RETRY_POLICY = RetryPolicy(retry_on=_is_retryable, max_attempts=3)

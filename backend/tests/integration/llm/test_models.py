"""LLM呼び出し（成功・失敗・タイムアウト）のIT。

実際のLLM APIに接続する（backend-python.md 6節の「常にモック」の唯一の例外）。
費用・実行時間を抑えるため、`build_reply_model()`単体を対象にし（チャットAPI経由だと
話者選択・応答生成・タイトル生成で複数回呼ばれうるため）、失敗・タイムアウトのケースは
実際の生成が始まる前にエラーになるよう仕向けている。

安価なモデルへの切り替えは`.env`の`IT_REPLY_MODEL`（`compose.it.yml`経由で`REPLY_MODEL`へ
渡る）で行う想定で、テスト側では追加の切り替えは行わない。
"""

import pytest
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from app.config import settings
from app.llm.models import _PROVIDER_API_KEYS, build_reply_model
from app.llm.retry import is_llm_api_error

_PROVIDER = settings.reply_model.split(":", 1)[0]


async def test_build_reply_model_succeeds_with_minimal_prompt() -> None:
    """最小限のプロンプトで実際に呼び出し、応答が返ってくることを確認する。"""
    model = build_reply_model()

    response = await model.ainvoke(
        [HumanMessage(content="「はい」とだけ返信してください。")]
    )

    assert isinstance(response.content, str)
    assert response.content.strip() != ""


async def test_reply_model_call_with_invalid_api_key_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """APIキーが不正な場合、実際の生成を待たずに認証エラーで失敗する（低コスト）。

    `retry.py`の`is_llm_api_error`がLLM呼び出し由来の失敗として正しく分類できることも
    あわせて確認する。
    """
    monkeypatch.setattr(settings, f"{_PROVIDER}_api_key", "invalid-key-for-it")
    model = build_reply_model()

    try:
        await model.ainvoke([HumanMessage(content="hi")])
    except Exception as exc:  # noqa: BLE001 - プロバイダ非依存で分類したいため広く受ける
        assert is_llm_api_error(exc)
    else:
        raise AssertionError("不正なAPIキーで呼び出しても例外が発生しなかった")


async def test_reply_model_call_times_out() -> None:
    """極端に短いタイムアウトを指定すると、生成を待たずタイムアウトで失敗する（低コスト）。

    `build_reply_model()`はタイムアウトを外から指定できないため、ここでは
    `init_chat_model`を直接使い同じプロバイダ・モデル・APIキーへ短いタイムアウトのみ
    追加する。
    """
    model = init_chat_model(
        settings.reply_model,
        api_key=_PROVIDER_API_KEYS.get(_PROVIDER),
        max_retries=0,
        timeout=0.001,
    )

    try:
        await model.ainvoke([HumanMessage(content="hi")])
    except Exception as exc:  # noqa: BLE001 - プロバイダ非依存で分類したいため広く受ける
        assert is_llm_api_error(exc)
    else:
        raise AssertionError("極端に短いタイムアウトでも例外が発生しなかった")

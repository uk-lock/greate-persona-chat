"""`app/llm/models.py`の単体テスト。

`init_chat_model`（langchain）は呼び出しをモックし、実際のプロバイダAPIには接続しない。
"""

from unittest.mock import MagicMock

import pytest

from app.llm import models as models_module
from app.llm.models import build_reply_model, build_selection_model, build_title_model


@pytest.fixture(autouse=True)
def mock_init_chat_model(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock()
    monkeypatch.setattr(models_module, "init_chat_model", mock)
    return mock


class TestBuildModels:
    def test_build_reply_model_uses_settings_reply_model(
        self, monkeypatch: pytest.MonkeyPatch, mock_init_chat_model: MagicMock
    ) -> None:
        monkeypatch.setattr(models_module.settings, "reply_model", "openai:gpt-5-mini")
        monkeypatch.setattr(models_module, "_PROVIDER_API_KEYS", {"openai": "sk-reply"})

        build_reply_model()

        mock_init_chat_model.assert_called_once_with(
            "openai:gpt-5-mini", api_key="sk-reply", max_retries=0
        )

    def test_build_selection_model_uses_settings_selection_model(
        self, monkeypatch: pytest.MonkeyPatch, mock_init_chat_model: MagicMock
    ) -> None:
        monkeypatch.setattr(
            models_module.settings, "selection_model", "deepseek:deepseek-chat"
        )
        monkeypatch.setattr(
            models_module, "_PROVIDER_API_KEYS", {"deepseek": "sk-selection"}
        )

        build_selection_model()

        mock_init_chat_model.assert_called_once_with(
            "deepseek:deepseek-chat", api_key="sk-selection", max_retries=0
        )

    def test_build_title_model_uses_settings_title_model(
        self, monkeypatch: pytest.MonkeyPatch, mock_init_chat_model: MagicMock
    ) -> None:
        monkeypatch.setattr(models_module.settings, "title_model", "openai:gpt-5-nano")
        monkeypatch.setattr(models_module, "_PROVIDER_API_KEYS", {"openai": "sk-title"})

        build_title_model()

        mock_init_chat_model.assert_called_once_with(
            "openai:gpt-5-nano", api_key="sk-title", max_retries=0
        )

    def test_unknown_provider_passes_none_as_api_key(
        self, monkeypatch: pytest.MonkeyPatch, mock_init_chat_model: MagicMock
    ) -> None:
        """未対応プロバイダの場合、api_keyはNoneのまま`init_chat_model`へ渡される。"""
        monkeypatch.setattr(models_module.settings, "reply_model", "anthropic:claude-x")
        monkeypatch.setattr(models_module, "_PROVIDER_API_KEYS", {"openai": "sk-x"})

        build_reply_model()

        mock_init_chat_model.assert_called_once_with(
            "anthropic:claude-x", api_key=None, max_retries=0
        )

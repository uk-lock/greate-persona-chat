"""`app/llm/retry.py`の単体テスト。

LLMプロバイダSDKに依存しない、プロバイダ非依存の例外判定ロジックの単体テスト。
"""

import pytest

from app.llm.retry import _is_retryable, is_llm_api_error


class _StatusCodeError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code


class APITimeoutError(Exception):
    """プロバイダSDKのタイムアウト例外を模した、型名一致で判定されるクラス。"""


class APIConnectionError(Exception):
    """プロバイダSDKの接続エラー例外を模した、型名一致で判定されるクラス。"""


class TestIsLlmApiError:
    @pytest.mark.parametrize(
        "exc",
        [
            TimeoutError("timeout"),
            ConnectionError("connection"),
            APITimeoutError(),
            APIConnectionError(),
            _StatusCodeError(500),
            _StatusCodeError(400),
        ],
    )
    def test_returns_true_for_llm_related_errors(self, exc: Exception) -> None:
        assert is_llm_api_error(exc) is True

    @pytest.mark.parametrize(
        "exc",
        [
            ValueError("unrelated"),
            KeyError("missing"),
            RuntimeError("invariant violation"),
        ],
    )
    def test_returns_false_for_unrelated_errors(self, exc: Exception) -> None:
        assert is_llm_api_error(exc) is False

    def test_returns_false_when_status_code_is_not_an_int(self) -> None:
        """`status_code`属性があっても型がintでなければLLMエラー扱いしない（境界）。"""

        class _NonIntStatusCode(Exception):
            status_code = "500"

        assert is_llm_api_error(_NonIntStatusCode()) is False


class TestIsRetryable:
    @pytest.mark.parametrize(
        "exc",
        [
            TimeoutError("timeout"),
            ConnectionError("connection"),
            APITimeoutError(),
            APIConnectionError(),
            _StatusCodeError(500),
            _StatusCodeError(429),
        ],
    )
    def test_returns_true_for_transient_errors(self, exc: Exception) -> None:
        assert _is_retryable(exc) is True

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404])
    def test_returns_false_for_client_errors(self, status_code: int) -> None:
        """4xxクライアントエラー（429を除く）は再試行しない。"""
        assert _is_retryable(_StatusCodeError(status_code)) is False

    @pytest.mark.parametrize("status_code", [500, 502, 503, 429])
    def test_returns_true_at_boundary_status_codes(self, status_code: int) -> None:
        """境界値：5xx全般および429は再試行対象。"""
        assert _is_retryable(_StatusCodeError(status_code)) is True

    def test_returns_false_for_unrelated_error(self) -> None:
        assert _is_retryable(ValueError("unrelated")) is False

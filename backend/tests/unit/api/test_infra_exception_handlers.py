"""`app/api/infra_exception_handlers.py`の単体テスト。

`RateLimitExceeded`は`limit`/`error_message`の実際の内部構造に依存させず、
`_rate_limit_exceeded_handler`が読み取る属性のみを持つダミー例外で代替する。
"""

import json
from unittest.mock import MagicMock

from app.api.infra_exception_handlers import (
    _DEFAULT_RATE_LIMIT_MESSAGE,
    _rate_limit_exceeded_handler,
    register_infra_exception_handlers,
)


def _exc_with_error_message(message: str | None) -> Exception:
    exc = MagicMock(spec=["limit"])
    exc.limit = MagicMock(spec=["error_message"])
    exc.limit.error_message = message
    return exc


class TestRateLimitExceededHandler:
    async def test_uses_error_message_from_matched_limit(self) -> None:
        response = await _rate_limit_exceeded_handler(
            MagicMock(), _exc_with_error_message("送信回数が上限に達しました。")
        )

        assert response.status_code == 429
        assert json.loads(bytes(response.body)) == {
            "message": "送信回数が上限に達しました。"
        }

    async def test_falls_back_to_default_when_error_message_is_none(self) -> None:
        response = await _rate_limit_exceeded_handler(
            MagicMock(), _exc_with_error_message(None)
        )

        assert json.loads(bytes(response.body)) == {
            "message": _DEFAULT_RATE_LIMIT_MESSAGE
        }

    async def test_falls_back_to_default_when_limit_attribute_is_missing(self) -> None:
        """`limit`/`error_message`の内部構造が想定外でも500にせず安全側に倒す。"""
        exc = MagicMock(spec=[])

        response = await _rate_limit_exceeded_handler(MagicMock(), exc)

        assert json.loads(bytes(response.body)) == {
            "message": _DEFAULT_RATE_LIMIT_MESSAGE
        }


class TestRegisterInfraExceptionHandlers:
    def test_registers_handler_for_rate_limit_exceeded(self) -> None:
        from slowapi.errors import RateLimitExceeded

        app = MagicMock()

        register_infra_exception_handlers(app)

        app.add_exception_handler.assert_called_once_with(
            RateLimitExceeded, _rate_limit_exceeded_handler
        )

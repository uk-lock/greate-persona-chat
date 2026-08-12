"""`app/api/app_exception_handlers.py`の単体テスト。

`_app_error_handler`はリクエストの中身を参照しないため、`request`引数はダミーで足りる。
"""

import json
from unittest.mock import MagicMock

import pytest

from app.api.app_exception_handlers import (
    _app_error_handler,
    register_app_exception_handlers,
)
from app.services.exceptions import (
    AppError,
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    UserLockedError,
    ValidationError,
)


class _UnmappedError(AppError):
    """`EXCEPTION_STATUS_MAP`に登録されていない業務例外（境界値の検証用）。"""


class TestAppErrorHandler:
    @pytest.mark.parametrize(
        ("exc_type", "expected_status"),
        [
            (NotFoundError, 404),
            (ConflictError, 409),
            (UnauthorizedError, 401),
            (UserLockedError, 423),
            (ForbiddenError, 403),
            (ValidationError, 400),
            (ExternalServiceError, 502),
        ],
    )
    async def test_maps_known_app_errors_to_status_code(
        self, exc_type: type[AppError], expected_status: int
    ) -> None:
        response = await _app_error_handler(
            MagicMock(), exc_type("エラーが発生しました")
        )

        assert response.status_code == expected_status
        assert json.loads(bytes(response.body)) == {"message": "エラーが発生しました"}

    async def test_unmapped_app_error_falls_back_to_500(self) -> None:
        """境界値：対応表に無いAppErrorサブクラスは500として扱う。"""
        response = await _app_error_handler(MagicMock(), _UnmappedError("未知のエラー"))

        assert response.status_code == 500


class TestRegisterAppExceptionHandlers:
    def test_registers_handler_for_app_error(self) -> None:
        app = MagicMock()

        register_app_exception_handlers(app)

        app.add_exception_handler.assert_called_once_with(AppError, _app_error_handler)

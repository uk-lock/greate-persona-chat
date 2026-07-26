"""AppError系例外をHTTPレスポンスへ変換する例外ハンドラ。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    UserLockedError,
    ValidationError,
)

EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    UnauthorizedError: 401,
    UserLockedError: 423,
    ForbiddenError: 403,
    ValidationError: 400,
}
"""業務例外クラスとHTTPステータスコードの対応表（backend-python.md 10節）。"""


async def _app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """AppError系例外を`{"message": "string"}`形式のレスポンスへ変換する。"""
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"message": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """AppError用の例外ハンドラをアプリへ登録する。"""
    app.add_exception_handler(AppError, _app_error_handler)

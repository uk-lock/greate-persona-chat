"""インフラ層（ライブラリ由来）の例外をHTTPレスポンスへ変換する例外ハンドラ。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def _rate_limit_exceeded_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """レート制限超過を、共通のエラーレスポンス形式（common.md6節）へ変換する。"""
    return JSONResponse(
        status_code=429,
        content={
            "message": "リクエストが多すぎます。しばらくしてから再度お試しください。"
        },
    )


def register_infra_exception_handlers(app: FastAPI) -> None:
    """ライブラリ由来の例外用ハンドラをアプリへ登録する。"""
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

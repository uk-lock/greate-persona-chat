"""インフラ層（ライブラリ由来）の例外をHTTPレスポンスへ変換する例外ハンドラ。"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


_DEFAULT_RATE_LIMIT_MESSAGE = "リクエストが多すぎます。しばらくしてから再度お試しください。"


async def _rate_limit_exceeded_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """レート制限超過を、共通のエラーレスポンス形式（common.md6節）へ変換する。

    どの制限（短時間／1日等）に該当したかが分かる文言を返すため（S03-chat.md 7節）、
    該当する`@limiter.limit()`に設定した`error_message`を使う。取得できない場合は
    汎用文言にフォールバックする（`limit`/`error_message`はslowapiの内部実装に
    依存するため、想定外の構造でも500にせず安全側に倒す）。
    """
    message = (
        getattr(getattr(exc, "limit", None), "error_message", None)
        or _DEFAULT_RATE_LIMIT_MESSAGE
    )
    return JSONResponse(status_code=429, content={"message": message})


def register_infra_exception_handlers(app: FastAPI) -> None:
    """ライブラリ由来の例外用ハンドラをアプリへ登録する。"""
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

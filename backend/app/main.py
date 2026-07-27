"""FastAPIアプリケーションのエントリポイント。"""

from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware

from app.api.app_exception_handlers import register_app_exception_handlers
from app.api.infra_exception_handlers import register_infra_exception_handlers
from app.api.rate_limit import limiter
from app.api.routers import auth, chats, personas

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

app = FastAPI()

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

register_app_exception_handlers(app)
register_infra_exception_handlers(app)


@app.middleware("http")
async def verify_origin_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """状態変更リクエストのOriginヘッダーを検証する（CSRF対策、backend-python.md 15節）。

    同一サイト運用（フロント・バックエンドが同じサイトとして動く）前提のため、
    Originがhostと一致しない場合のみ拒否する。ブラウザ以外や一部の同一サイト
    リクエストではOriginヘッダー自体が省略され得るため、その場合は許容する。
    """
    if request.method in _UNSAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and urlsplit(origin).netloc != request.headers.get(
            "host"
        ):
            return JSONResponse(
                status_code=403, content={"message": "不正なリクエストです"}
            )
    return await call_next(request)


app.include_router(auth.router)
app.include_router(personas.router)
app.include_router(chats.router)

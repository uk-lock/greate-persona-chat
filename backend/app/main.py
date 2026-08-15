"""FastAPIアプリケーションのエントリポイント。"""

from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

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


class VerifyOriginHeaderMiddleware:
    """状態変更リクエストのOriginヘッダーを検証する（CSRF対策、backend-python.md 15節）。

    同一サイト運用（フロント・バックエンドが同じサイトとして動く）前提のため、
    Originがhostと一致しない場合のみ拒否する。ブラウザ以外や一部の同一サイト
    リクエストではOriginヘッダー自体が省略され得るため、その場合は許容する。

    `@app.middleware("http")`（Starletteの`BaseHTTPMiddleware`）ではなく、純粋な
    ASGIミドルウェアとして実装している。`BaseHTTPMiddleware`はレスポンスを別タスクで
    ラップする実装のため、クライアント切断等によるリクエストキャンセル時にキャンセル伝播が
    正しく行われず、そのとき使用中だったDBコネクションプールのコネクションが破損した状態で
    プールに戻ってしまうことがある（E2E導入時に、無関係な後続リクエストが
    `connection is closed`で500になる形で発覚。Starletteの既知の問題）。
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in _UNSAFE_METHODS:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if origin is not None and urlsplit(origin).netloc != headers.get("host"):
            response = JSONResponse(
                status_code=403, content={"message": "不正なリクエストです"}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


app.add_middleware(VerifyOriginHeaderMiddleware)

app.include_router(auth.router)
app.include_router(personas.router)
app.include_router(chats.router)

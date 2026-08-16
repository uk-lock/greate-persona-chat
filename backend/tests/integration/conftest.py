"""IT（結合テスト）共通のfixture。

実DB（`DATABASE_URL`環境変数で指定された接続先。Neonの専用テストブランチ等）に対して
実際にクエリを行う（backend-python.md 6節）。各テストはトランザクションでラップし、
テスト終了時にロールバックすることで共有DBを汚さないようにする
（SQLAlchemyの「外部トランザクションへのSessionの参加」パターン）。
"""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies import get_db
from app.api.rate_limit import limiter
from app.config import asyncpg_database_url
from app.main import app
from app.models.persona import Persona

# NullPool：pytest-asyncioはデフォルトでテスト関数ごとに新しいイベントループを使うため、
# 通常のコネクションプールだと前のテストのイベントループに紐付いた接続が使い回されて
# `RuntimeError: ... attached to a different loop`になる（migrations/env.pyと同じ理由）。
_engine = create_async_engine(asyncpg_database_url(), poolclass=pool.NullPool)


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """テストごとにレート制限（slowapi、インメモリ）をリセットする。

    未認証エンドポイント（サインアップ等）はIPアドレス単位でカウントされるが、
    `TestClient`からのリクエストは同一IP扱いになるため、リセットしないとIT間で
    カウントが積み上がり、無関係なテストがレート制限で失敗しうる（backend-python.md 16節）。
    """
    limiter.reset()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """1テスト1トランザクションのAsyncSessionを払い出し、終了時にロールバックする。

    アプリコード側（`get_db`）はリクエストの正常終了時に`session.commit()`を呼ぶが、
    ここではSessionを外側のコネクションのトランザクションへSAVEPOINTとして参加させることで、
    アプリ側のcommitを無害化する。1テスト内で複数リクエストがcommitを重ねても
    SAVEPOINTを都度張り直すことで動作を継続させ、最終的なrollbackで全体を巻き戻す。
    """
    async with _engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        session_factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        session = session_factory()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sync_session: object, transaction: object) -> None:
            if conn.closed:
                return
            if not conn.sync_connection.in_nested_transaction():
                conn.sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """実DBを使うAPI結合テスト用の非同期クライアント。`get_db`を`db_session`へ差し替える。

    FastAPIの`TestClient`（同期ラッパー）はリクエストごとに別のイベントループを使うことがあり、
    `db_session`のasyncpgコネクションと別ループに紐付いて`RuntimeError`になる
    （既知の相性問題）。`httpx.AsyncClient`でテスト自体を非同期にし、アプリ・DBコネクションを
    同一イベントループ上で動かすことで回避する。
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = httpx.ASGITransport(app=app)
    try:
        # 認証Cookieはsecure=True（app/api/routers/auth.py）のため、http://だと
        # 2回目以降のリクエストでhttpxのCookieジャーが送り返してくれない。
        async with httpx.AsyncClient(
            transport=transport, base_url="https://testserver"
        ) as async_client:
            yield async_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def make_login_id() -> Callable[[], str]:
    """テストごとに衝突しないlogin_idを生成するファクトリを返す。"""

    def _make() -> str:
        return f"it{uuid.uuid4().hex[:16]}"

    return _make


@pytest.fixture
def make_persona(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[Persona]]:
    """DBにペルソナを1件作成するファクトリを返す（idはDB側のシーケンス採番）。

    `tests/factories.py`のUT用ビルダーはidを決め打ちしており実DBへは使えないため、
    IT用に別途最小限のフィクスチャを用意する。複数ペルソナの並び順検証等、
    `persona`フィクスチャ1件だけでは足りないテストのために呼び出し側で使う。
    """

    async def _make(**overrides: Any) -> Persona:
        defaults: dict[str, Any] = {
            "name": "ペルソナ",
            "country": "日本",
            "era": "現代",
            "is_deleted": False,
            "created_by": "it",
            "updated_by": "it",
        }
        defaults.update(overrides)
        entity = Persona(**defaults)
        db_session.add(entity)
        await db_session.flush()
        return entity

    return _make


@pytest_asyncio.fixture
async def persona(make_persona: Callable[..., Awaitable[Persona]]) -> Persona:
    """DBに1件だけペルソナを作成して返す（`make_persona`の既定値版）。"""
    return await make_persona(name="ソクラテス", country="ギリシャ", era="古代")

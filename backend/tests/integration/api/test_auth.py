"""認証フロー（サインアップ→ログイン→ログアウト）のIT。実DBに対してAPI経由で検証する。"""

from collections.abc import Callable

import httpx

from app.config import constants


async def test_signup_then_login_succeeds(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """サインアップ後、同じ認証情報でログインでき、Cookieに認証トークンが設定される。"""
    login_id = make_login_id()
    password = "password123"

    signup_response = await client.post(
        "/auth/signup", json={"login_id": login_id, "password": password}
    )
    assert signup_response.status_code == 201
    assert constants.AUTH_COOKIE_NAME in signup_response.cookies

    client.cookies.clear()
    login_response = await client.post(
        "/auth/login", json={"login_id": login_id, "password": password}
    )
    assert login_response.status_code == 200
    assert constants.AUTH_COOKIE_NAME in login_response.cookies


async def test_login_with_wrong_password_returns_401(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """誤ったパスワードでのログインは401になる。"""
    login_id = make_login_id()
    await client.post(
        "/auth/signup", json={"login_id": login_id, "password": "password123"}
    )
    client.cookies.clear()

    response = await client.post(
        "/auth/login", json={"login_id": login_id, "password": "wrong-password"}
    )

    assert response.status_code == 401


async def test_signup_with_duplicate_login_id_returns_409(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """既に使用中のlogin_idでサインアップすると409になる（実DBのユニーク制約経由の検証を含む）。"""
    login_id = make_login_id()
    body = {"login_id": login_id, "password": "password123"}

    first = await client.post("/auth/signup", json=body)
    assert first.status_code == 201

    second = await client.post("/auth/signup", json=body)
    assert second.status_code == 409


async def test_repeated_login_failures_locks_account(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """`LOGIN_FAILURE_LIMIT`回連続でログインに失敗すると、正しいパスワードでも423になる。

    各失敗レスポンスはサービス層が意図して送出する`UnauthorizedError`（401）経由だが、
    その際に加算される`failed_login_count`自体はリクエストをまたいでDBへ永続化されて
    いる必要がある（`get_db`がAppError発生時もcommitすることの回帰テスト。
    以前はrollbackされてしまい、何回失敗してもロックされないバグがあった）。
    """
    login_id = make_login_id()
    password = "password123"
    await client.post("/auth/signup", json={"login_id": login_id, "password": password})
    client.cookies.clear()

    for _ in range(constants.LOGIN_FAILURE_LIMIT):
        response = await client.post(
            "/auth/login", json={"login_id": login_id, "password": "wrong-password"}
        )
        assert response.status_code == 401

    locked_response = await client.post(
        "/auth/login", json={"login_id": login_id, "password": password}
    )
    assert locked_response.status_code == 423


async def test_logout_clears_auth_cookie(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """ログアウト後は認証Cookieが破棄され、以降の認証必須エンドポイントは401になる。

    `logout`自体はDB・service層に一切依存しない（backend/app/api/routers/auth.py）ため、
    「実際にログイン状態が解除されるか」という振る舞いを、認証必須エンドポイント
    （`GET /personas`）への呼び出し結果で確認する（Set-Cookieヘッダーの中身を
    直接検証するより実体に即しているため）。
    """
    login_id = make_login_id()
    signup_response = await client.post(
        "/auth/signup", json={"login_id": login_id, "password": "password123"}
    )
    assert signup_response.status_code == 201

    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 200

    response = await client.get("/personas")
    assert response.status_code == 401

"""ペルソナ取得のIT。API→DB取得までを実DBで検証する。"""

from collections.abc import Callable

import httpx

from app.models.persona import Persona


async def _signup(client: httpx.AsyncClient, make_login_id: Callable[[], str]) -> None:
    login_id = make_login_id()
    response = await client.post(
        "/auth/signup", json={"login_id": login_id, "password": "password123"}
    )
    assert response.status_code == 201


async def test_get_personas_returns_saved_persona(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """DBに保存済みのペルソナが一覧APIで取得できる（API→DB保存→取得の結合）。"""
    await _signup(client, make_login_id)

    response = await client.get("/personas")

    assert response.status_code == 200
    body = response.json()
    assert any(
        item["id"] == persona.id and item["name"] == persona.name for item in body
    )


async def test_get_persona_by_id_returns_detail(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """存在するペルソナidで詳細を取得できる。"""
    await _signup(client, make_login_id)

    response = await client.get(f"/personas/{persona.id}")

    assert response.status_code == 200
    assert response.json()["name"] == persona.name


async def test_get_persona_by_unknown_id_returns_404(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """存在しないペルソナidを指定すると404になる。"""
    await _signup(client, make_login_id)

    response = await client.get("/personas/999999999")

    assert response.status_code == 404


async def test_get_personas_without_auth_returns_401(client: httpx.AsyncClient) -> None:
    """未認証（Cookie無し）でのアクセスは401になる。"""
    response = await client.get("/personas")

    assert response.status_code == 401

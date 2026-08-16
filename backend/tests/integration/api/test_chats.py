"""チャットCRUDのIT。API→DB保存→取得、認可、バリデーションを実DBで検証する。"""

import uuid
from collections.abc import Awaitable, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.chat_message import ChatMessage, SpeakerType
from app.models.persona import Persona


async def _signup(client: httpx.AsyncClient, make_login_id: Callable[[], str]) -> str:
    login_id = make_login_id()
    response = await client.post(
        "/auth/signup", json={"login_id": login_id, "password": "password123"}
    )
    assert response.status_code == 201
    return login_id


async def _login(
    client: httpx.AsyncClient, login_id: str, password: str = "password123"
) -> None:
    response = await client.post(
        "/auth/login", json={"login_id": login_id, "password": password}
    )
    assert response.status_code == 200


async def test_create_chat_then_get_roundtrips_through_db(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """作成したチャットをDB経由で取得でき、参加ペルソナ・メッセージ0件が反映される
    （API→DB保存→取得の結合）。"""
    await _signup(client, make_login_id)

    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "哲学について",
        },
    )
    assert create_response.status_code == 201
    chat_id = create_response.json()["chat_id"]

    get_response = await client.get(f"/chats/{chat_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["chat_id"] == chat_id
    assert body["topic"] == "哲学について"
    assert [p["persona_id"] for p in body["participants"]] == [persona.id]

    messages_response = await client.get(f"/chats/{chat_id}/messages")
    assert messages_response.status_code == 200
    assert messages_response.json() == []


async def test_delete_chat_then_get_returns_404(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """削除（論理削除）したチャットはその後の取得で404になる。"""
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_id = create_response.json()["chat_id"]

    delete_response = await client.delete(f"/chats/{chat_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/chats/{chat_id}")
    assert get_response.status_code == 404


async def test_get_chats_without_auth_returns_401(client: httpx.AsyncClient) -> None:
    """未認証（Cookie無し）でのアクセスは401になる。"""
    response = await client.get("/chats")

    assert response.status_code == 401


async def test_get_chats_returns_only_current_users_chats(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """チャット一覧は自分が作成したものだけが返る（他ユーザーのチャットは含まれない）。"""
    other_login_id = await _signup(client, make_login_id)
    other_create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "他ユーザーのチャット",
        },
    )
    other_chat_id = other_create_response.json()["chat_id"]

    client.cookies.clear()
    await _signup(client, make_login_id)
    own_create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "自分のチャット",
        },
    )
    own_chat_id = own_create_response.json()["chat_id"]

    list_response = await client.get("/chats")

    assert list_response.status_code == 200
    chat_ids = [c["chat_id"] for c in list_response.json()]
    assert own_chat_id in chat_ids
    assert other_chat_id not in chat_ids

    # ownerが再ログインしても自分のチャットしか見えないことも確認しておく
    client.cookies.clear()
    await _login(client, other_login_id)
    other_list_response = await client.get("/chats")
    other_chat_ids = [c["chat_id"] for c in other_list_response.json()]
    assert other_chat_id in other_chat_ids
    assert own_chat_id not in other_chat_ids


async def test_other_users_chat_is_forbidden(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """他ユーザーが作成したチャットの取得・削除は403になる。"""
    owner_login_id = await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_id = create_response.json()["chat_id"]

    # 別ユーザーとしてログインし直す（ownerのセッションと入れ替える）
    client.cookies.clear()
    await _signup(client, make_login_id)

    get_response = await client.get(f"/chats/{chat_id}")
    assert get_response.status_code == 403

    delete_response = await client.delete(f"/chats/{chat_id}")
    assert delete_response.status_code == 403

    # ownerがまだ実際にアクセスできる（対象自体は生きている）ことも確認しておく
    client.cookies.clear()
    await _login(client, owner_login_id)
    owner_get_response = await client.get(f"/chats/{chat_id}")
    assert owner_get_response.status_code == 200


async def test_create_chat_with_too_many_personas_returns_422(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """参加ペルソナ数が上限（5体）を超えるとバリデーションエラーになる。"""
    await _signup(client, make_login_id)

    response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id] * 6,
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )

    assert response.status_code == 422


async def test_create_persona_only_chat_without_topic_returns_422(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """PERSONA_ONLYモードでtopic未指定だとバリデーションエラーになる。"""
    await _signup(client, make_login_id)

    response = await client.post(
        "/chats",
        json={"persona_ids": [persona.id], "chat_mode": "PERSONA_ONLY"},
    )

    assert response.status_code == 422


async def test_create_chat_with_multiple_personas_preserves_order(
    client: httpx.AsyncClient,
    make_persona: Callable[..., Awaitable[Persona]],
    make_login_id: Callable[[], str],
) -> None:
    """複数ペルソナを指定した順序（sort_no）が、作成レスポンス・取得の両方で保たれる
    （ChatPersonaRepositoryの並び順検証）。"""
    persona_b = await make_persona(name="ペルソナB")
    persona_a = await make_persona(name="ペルソナA")
    await _signup(client, make_login_id)

    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona_b.id, persona_a.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert [p["persona_id"] for p in body["participants"]] == [
        persona_b.id,
        persona_a.id,
    ]

    get_response = await client.get(f"/chats/{body['chat_id']}")
    assert get_response.status_code == 200
    assert [p["persona_id"] for p in get_response.json()["participants"]] == [
        persona_b.id,
        persona_a.id,
    ]


async def test_get_messages_returns_in_sort_no_order(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """メッセージがsort_no順で返る（ChatMessageRepositoryの並び順検証）。

    メッセージ送信APIは実LLM呼び出しを伴う（tests/integration/llm/参照）ため、
    ここでは並び順だけを検証したく、DBへ直接メッセージ行を挿入する。
    """
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_public_id = create_response.json()["chat_id"]
    internal_chat_id = (
        await db_session.execute(
            select(Chat.id).where(Chat.public_id == chat_public_id)
        )
    ).scalar_one()

    db_session.add_all(
        [
            ChatMessage(
                chat_id=internal_chat_id,
                persona_id=persona.id,
                sort_no=2,
                speaker_type=SpeakerType.PERSONA,
                message="2番目の発言",
                created_by="it",
                updated_by="it",
            ),
            ChatMessage(
                chat_id=internal_chat_id,
                persona_id=None,
                sort_no=1,
                speaker_type=SpeakerType.USER,
                message="1番目の発言",
                created_by="it",
                updated_by="it",
            ),
        ]
    )
    await db_session.flush()

    response = await client.get(f"/chats/{chat_public_id}/messages")

    assert response.status_code == 200
    body = response.json()
    assert [m["sort_no"] for m in body] == [1, 2]
    assert [m["message"] for m in body] == ["1番目の発言", "2番目の発言"]


async def test_stop_chat_without_auth_returns_401(client: httpx.AsyncClient) -> None:
    """未認証での中断リクエストは401になる。"""
    response = await client.post(f"/chats/{uuid.uuid4()}/stop")

    assert response.status_code == 401


async def test_stop_unknown_chat_returns_404(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """存在しないチャットの中断は404になる。"""
    await _signup(client, make_login_id)

    response = await client.post(f"/chats/{uuid.uuid4()}/stop")

    assert response.status_code == 404


async def test_stop_other_users_chat_returns_403(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """他ユーザーのチャットの中断は403になる。"""
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_id = create_response.json()["chat_id"]

    client.cookies.clear()
    await _signup(client, make_login_id)

    response = await client.post(f"/chats/{chat_id}/stop")

    assert response.status_code == 403


async def test_stop_owned_chat_succeeds(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """自分のチャットの中断は204になる。"""
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_id = create_response.json()["chat_id"]

    response = await client.post(f"/chats/{chat_id}/stop")

    assert response.status_code == 204


async def test_post_message_without_auth_returns_401(client: httpx.AsyncClient) -> None:
    """未認証でのメッセージ送信は401になる（LLM呼び出しに到達しない）。"""
    response = await client.post(
        f"/chats/{uuid.uuid4()}/messages", json={"message": "こんにちは"}
    )

    assert response.status_code == 401


async def test_post_message_to_unknown_chat_returns_404(
    client: httpx.AsyncClient, make_login_id: Callable[[], str]
) -> None:
    """存在しないチャットへのメッセージ送信は404になる（LLM呼び出しに到達しない）。"""
    await _signup(client, make_login_id)

    response = await client.post(
        f"/chats/{uuid.uuid4()}/messages", json={"message": "こんにちは"}
    )

    assert response.status_code == 404


async def test_post_message_to_other_users_chat_returns_403(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """他ユーザーのチャットへのメッセージ送信は403になる（LLM呼び出しに到達しない）。"""
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={
            "persona_ids": [persona.id],
            "chat_mode": "PERSONA_ONLY",
            "topic": "お題",
        },
    )
    chat_id = create_response.json()["chat_id"]

    client.cookies.clear()
    await _signup(client, make_login_id)

    response = await client.post(
        f"/chats/{chat_id}/messages", json={"message": "こんにちは"}
    )

    assert response.status_code == 403


async def test_post_empty_message_in_user_participated_chat_returns_400(
    client: httpx.AsyncClient,
    persona: Persona,
    make_login_id: Callable[[], str],
) -> None:
    """USER_PARTICIPATEDモードで本文が空のメッセージ送信は400になる
    （USER発言の保存はStreamingResponse開始前に行われるため、LLM呼び出しに到達しない。
    app/api/routers/chats.pyの`post_message`docstring参照）。"""
    await _signup(client, make_login_id)
    create_response = await client.post(
        "/chats",
        json={"persona_ids": [persona.id], "chat_mode": "USER_PARTICIPATED"},
    )
    chat_id = create_response.json()["chat_id"]

    response = await client.post(f"/chats/{chat_id}/messages", json={"message": "  "})

    assert response.status_code == 400

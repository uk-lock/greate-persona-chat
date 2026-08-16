"""m_user・m_personaへの初期データ投入ツール（DB直接投入）。

管理画面はMVP対象外でDB直接投入前提のため（docs/screen-list.md 4節）、
動作確認用の初期ユーザ（backend/data/init_user.json）と
偉人ペルソナ（backend/data/init_persona.json）をまとめてDBへ反映する。

使い方:
    docker compose exec backend python -m tools.insert_init_data

backend/data/init_user.jsonは{"login_id": "string", "password": "string"}の1件のみ。
既に同じlogin_idのユーザが存在する場合は何もしない（べき等）。

backend/data/init_persona.jsonの各要素はm_persona（docs/db.md参照）に対応する。`name`のみ
必須で、他の項目は省略可（省略時はNULLとして登録する）。

```json
[
  {
    "name": "string",
    "image_url": "string",
    "country": "string",
    "era": "string",
    "summary": "string",
    "description": "string",
    "personality": "string",
    "conversation_policy": "string",
    "biography": [{"year": 1780, "event": "string"}, "..."],
    "sample_quotes": ["string", "..."]
  }
]
```

`conversation_policy`は会話のポジション・語尾等の会話生成向け方針をフリーテキストで
持たせる項目で、フロント側の画面には表示しない（LLMのプロンプト構築にのみ使う）。

ペルソナは逐次追加していく想定のため、同名（name）のペルソナが既に登録済みの場合は
スキップする（べき等。nameにDB上の一意制約はないため簡易的なチェックに留まる）。

`backend/data/`は投入用の一時的な作業ファイル置き場のためgit管理対象外（`.gitignore`）。
平文パスワードを含むため、本ファイルは各自のローカルで用意する。
投入後はDB側が正のデータであり、`init_user.json`・`init_persona.json`は各自のローカルで用意する。
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from argon2 import PasswordHasher
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.persona import Persona
from app.models.user import User
from app.repositories.persona_repository import PersonaRepository
from app.repositories.user_repository import UserRepository

_CREATED_BY = "seed_tool"
_LOGIN_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,255}$")
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_USER_DATA_FILE = _DATA_DIR / "init_user.json"
_PERSONA_DATA_FILE = _DATA_DIR / "init_persona.json"
_password_hasher = PasswordHasher()

# JSON由来の動的なペルソナ定義のため、値の型としてここでのみAnyを許容する
PersonaEntry = dict[str, Any]


def _validate_login_id(login_id: str) -> None:
    """login_idがm_user.login_idの制約（半角英数字・255文字以内）を満たすか検証する。

    Raises:
        ValueError: 制約に反する場合。
    """
    if not _LOGIN_ID_PATTERN.match(login_id):
        raise ValueError(
            "login_idは半角英数字・255文字以内である必要があります"
            "（docs/db.md m_user参照）"
        )


def _load_init_user() -> tuple[str, str]:
    """backend/data/init_user.jsonを読み込む。

    Returns:
        (login_id, password)のタプル。
    """
    with _USER_DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    login_id: str = data["login_id"]
    password: str = data["password"]
    return login_id, password


def _load_init_personas() -> list[PersonaEntry]:
    """backend/data/init_persona.jsonを読み込む。

    Returns:
        ペルソナ定義の一覧。
    """
    with _PERSONA_DATA_FILE.open(encoding="utf-8") as f:
        entries: list[PersonaEntry] = json.load(f)
    return entries


async def insert_init_user(session: AsyncSession) -> None:
    """backend/data/init_user.jsonの内容でm_userに初期ユーザを登録する。

    Raises:
        ValueError: login_idが文字種・文字数の制約に反する場合。
    """
    login_id, password = _load_init_user()
    _validate_login_id(login_id)

    repository = UserRepository(session)
    existing = await repository.get_by_login_id(login_id)
    if existing is not None:
        print(f"既に存在するため何もしません: login_id={login_id}")
        return

    user = User(
        login_id=login_id,
        password_hash=_password_hasher.hash(password),
        failed_login_count=0,
        locked_until=None,
        created_by=_CREATED_BY,
        updated_by=_CREATED_BY,
    )
    await repository.add(user)
    await session.commit()
    print(f"初期ユーザを登録しました: login_id={login_id}")


async def insert_init_persona(session: AsyncSession) -> None:
    """init_persona.jsonの内容をm_personaへ投入する（同名の既存レコードはスキップ）。"""
    repository = PersonaRepository(session)
    for entry in _load_init_personas():
        name = entry["name"]
        existing = await repository.get_by_name(name)
        if existing is not None:
            print(f"スキップ（登録済み）: {name}")
            continue

        persona = Persona(
            name=name,
            image_url=entry.get("image_url"),
            country=entry.get("country"),
            era=entry.get("era"),
            summary=entry.get("summary"),
            description=entry.get("description"),
            personality=entry.get("personality"),
            conversation_policy=entry.get("conversation_policy"),
            biography=entry.get("biography"),
            sample_quotes=entry.get("sample_quotes"),
            created_by=_CREATED_BY,
            updated_by=_CREATED_BY,
        )
        await repository.add(persona)
        print(f"登録しました: {name}")

    await session.commit()


async def insert_init_data() -> None:
    """初期ユーザ・ペルソナをまとめてDBへ投入する。"""
    engine = create_async_engine(
        make_url(settings.database_url)
        .set(drivername="postgresql+asyncpg")
        .render_as_string(hide_password=False)
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await insert_init_user(session)
        await insert_init_persona(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(insert_init_data())

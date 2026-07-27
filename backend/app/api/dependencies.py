"""DBセッション・JWT認証・repository/serviceのDIをまとめる依存注入モジュール。"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, Request
from slowapi.util import get_remote_address
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import constants, settings
from app.models.user import User
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.chat_persona_repository import ChatPersonaRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.exceptions import UnauthorizedError
from app.services.persona_service import PersonaService

_engine = create_async_engine(
    str(make_url(settings.database_url).set(drivername="postgresql+asyncpg"))
)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """リクエスト単位のAsyncSessionを払い出す。

    正常終了時はcommit、例外発生時はrollackする（backend-python.md 14節）。
    """
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_persona_repository(
    session: AsyncSession = Depends(get_db),
) -> PersonaRepository:
    return PersonaRepository(session)


def get_chat_repository(session: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(session)


def get_chat_persona_repository(
    session: AsyncSession = Depends(get_db),
) -> ChatPersonaRepository:
    return ChatPersonaRepository(session)


def get_chat_message_repository(
    session: AsyncSession = Depends(get_db),
) -> ChatMessageRepository:
    return ChatMessageRepository(session)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repository)


def get_persona_service(
    persona_repository: PersonaRepository = Depends(get_persona_repository),
) -> PersonaService:
    return PersonaService(persona_repository)


def get_chat_service(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    chat_persona_repository: ChatPersonaRepository = Depends(
        get_chat_persona_repository
    ),
    chat_message_repository: ChatMessageRepository = Depends(
        get_chat_message_repository
    ),
    persona_repository: PersonaRepository = Depends(get_persona_repository),
) -> ChatService:
    return ChatService(
        chat_repository,
        chat_persona_repository,
        chat_message_repository,
        persona_repository,
    )


def create_access_token(user: User) -> str:
    """ログイン成功後にJWTを発行する。

    Args:
        user: 認証済みユーザ。

    Returns:
        署名済みJWT文字列。
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(hours=constants.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=constants.JWT_ALGORITHM
    )


def _decode_user_id(token: str) -> int:
    """JWTを検証し、ペイロードからユーザidを取り出す。

    Raises:
        UnauthorizedError: トークンが不正・期限切れ、またはペイロードが不正な場合。
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[constants.JWT_ALGORITHM]
        )
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("認証が必要です") from exc
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise UnauthorizedError("認証が必要です") from exc


async def get_current_user(
    request: Request,
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Cookie中のJWTを検証し、ログイン中のユーザを取得する。

    Raises:
        UnauthorizedError: Cookieが無い、トークンが不正、またはユーザが存在しない場合。
    """
    token = request.cookies.get(constants.AUTH_COOKIE_NAME)
    if token is None:
        raise UnauthorizedError("認証が必要です")

    user_id = _decode_user_id(token)
    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("認証が必要です")
    return user


def get_user_id_for_rate_limit(request: Request) -> str:
    """レート制限のキーとして、Cookie中のJWTからユーザidを取り出す。

    slowapiのkey_funcはリクエストのみを受け取る同期関数であるため、DBアクセスは行わず
    JWTのデコードのみで済ませる（認証自体の正当性検証はget_current_userが別途行う）。
    トークンが無い・不正な場合はIPアドレスにフォールバックする。
    """
    token = request.cookies.get(constants.AUTH_COOKIE_NAME)
    if token is None:
        return get_remote_address(request)
    try:
        return str(_decode_user_id(token))
    except UnauthorizedError:
        return get_remote_address(request)

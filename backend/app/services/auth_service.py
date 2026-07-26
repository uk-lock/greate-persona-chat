"""認証（サインアップ・ログイン）に関するユースケース。"""

from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import constants, settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
    UserLockedError,
)

_password_hasher = PasswordHasher()


class AuthService:
    """m_userに対するサインアップ・ログインのユースケースを提供する。"""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def signup(self, login_id: str, password: str) -> User:
        """新規ユーザを登録する（自己登録）。

        Args:
            login_id: 登録するログインID（文字種・文字数のバリデーションはAPI層で実施済みの前提）。
            password: 平文パスワード。ハッシュ化してから保存する。

        Returns:
            作成されたユーザ。

        Raises:
            ForbiddenError: サインアップ機能が設定で無効化されている場合。
            ConflictError: login_idが既存ユーザと重複する場合。
        """
        if not settings.signup_enabled:
            raise ForbiddenError("現在サインアップは無効化されています")

        existing_user = await self._user_repository.get_by_login_id(login_id)
        if existing_user is not None:
            raise ConflictError("このログインIDは既に使用されています")

        user = User(
            login_id=login_id,
            password_hash=_password_hasher.hash(password),
            failed_login_count=0,
            locked_until=None,
            created_by=login_id,
            updated_by=login_id,
        )
        return await self._user_repository.add(user)

    async def login(self, login_id: str, password: str) -> User:
        """ログインID・パスワードを検証する。

        Args:
            login_id: ログインID。
            password: 平文パスワード。

        Returns:
            認証に成功したユーザ。

        Raises:
            UnauthorizedError: ログインIDが存在しない、またはパスワードが誤っている場合。
            UserLockedError: 連続失敗によりロック中の場合。
        """
        user = await self._user_repository.get_by_login_id(login_id)
        if user is None:
            raise UnauthorizedError("ログインIDまたはパスワードが正しくありません")

        now = datetime.now(UTC)
        if user.locked_until is not None:
            if user.locked_until > now:
                raise UserLockedError("連続ログイン失敗によりロックされています")
            # ロック期間が経過済みのため、判定前に一旦解除する
            user.failed_login_count = 0
            user.locked_until = None

        try:
            _password_hasher.verify(user.password_hash, password)
        except VerifyMismatchError:
            user.failed_login_count += 1
            if user.failed_login_count >= constants.LOGIN_FAILURE_LIMIT:
                user.locked_until = now + timedelta(
                    minutes=constants.LOGIN_LOCK_DURATION_MINUTES
                )
            user.updated_by = login_id
            await self._user_repository.flush()
            raise UnauthorizedError(
                "ログインIDまたはパスワードが正しくありません"
            ) from None

        user.failed_login_count = 0
        user.locked_until = None
        user.updated_by = login_id
        await self._user_repository.flush()
        return user

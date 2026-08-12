"""AuthService（サインアップ・ログイン）の単体テスト。

UserRepositoryはAsyncMockに置き換え、実DBには一切依存しない。
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from argon2 import PasswordHasher

from app.config import constants
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    UnauthorizedError,
    UserLockedError,
)
from tests.factories import make_user

_password_hasher = PasswordHasher()


@pytest.fixture
def user_repository() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def auth_service(user_repository: AsyncMock) -> AuthService:
    return AuthService(user_repository)


class TestSignup:
    async def test_signup_creates_user_when_enabled_and_not_duplicate(
        self, auth_service: AuthService, user_repository: AsyncMock, monkeypatch
    ) -> None:
        monkeypatch.setattr("app.services.auth_service.settings.signup_enabled", True)
        user_repository.get_by_login_id.return_value = None
        user_repository.add.side_effect = lambda user: user

        created = await auth_service.signup("alice", "password123")

        assert created.login_id == "alice"
        assert created.password_hash != "password123"  # 平文のまま保存されない
        assert created.failed_login_count == 0
        assert created.locked_until is None
        user_repository.add.assert_awaited_once()

    async def test_signup_raises_forbidden_when_disabled(
        self, auth_service: AuthService, user_repository: AsyncMock, monkeypatch
    ) -> None:
        monkeypatch.setattr("app.services.auth_service.settings.signup_enabled", False)

        with pytest.raises(ForbiddenError):
            await auth_service.signup("alice", "password123")

        user_repository.get_by_login_id.assert_not_awaited()
        user_repository.add.assert_not_awaited()

    async def test_signup_raises_conflict_when_login_id_duplicate(
        self, auth_service: AuthService, user_repository: AsyncMock, monkeypatch
    ) -> None:
        monkeypatch.setattr("app.services.auth_service.settings.signup_enabled", True)
        user_repository.get_by_login_id.return_value = make_user(login_id="alice")

        with pytest.raises(ConflictError):
            await auth_service.signup("alice", "password123")

        user_repository.add.assert_not_awaited()


class TestLogin:
    async def test_login_raises_unauthorized_when_user_not_found(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user_repository.get_by_login_id.return_value = None

        with pytest.raises(UnauthorizedError):
            await auth_service.login("ghost", "password123")

    async def test_login_succeeds_and_resets_failure_state(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=3,
            locked_until=None,
        )
        user_repository.get_by_login_id.return_value = user

        result = await auth_service.login("alice", "correct-password")

        assert result is user
        assert user.failed_login_count == 0
        assert user.locked_until is None
        user_repository.flush.assert_awaited_once()

    async def test_login_wrong_password_increments_failure_count_without_locking(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=3,
            locked_until=None,
        )
        user_repository.get_by_login_id.return_value = user

        with pytest.raises(UnauthorizedError):
            await auth_service.login("alice", "wrong-password")

        assert user.failed_login_count == 4
        assert user.locked_until is None
        user_repository.flush.assert_awaited_once()

    async def test_login_wrong_password_at_failure_limit_locks_user(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        """失敗回数が上限（境界値）に到達する失敗でロックされる。"""
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=constants.LOGIN_FAILURE_LIMIT - 1,
            locked_until=None,
        )
        user_repository.get_by_login_id.return_value = user

        before = datetime.now(UTC)
        with pytest.raises(UnauthorizedError):
            await auth_service.login("alice", "wrong-password")
        after = datetime.now(UTC)

        assert user.failed_login_count == constants.LOGIN_FAILURE_LIMIT
        assert user.locked_until is not None
        expected_min = before + timedelta(minutes=constants.LOGIN_LOCK_DURATION_MINUTES)
        expected_max = after + timedelta(minutes=constants.LOGIN_LOCK_DURATION_MINUTES)
        assert expected_min <= user.locked_until <= expected_max

    async def test_login_raises_user_locked_when_lock_still_active(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=constants.LOGIN_FAILURE_LIMIT,
            locked_until=datetime.now(UTC) + timedelta(minutes=1),
        )
        user_repository.get_by_login_id.return_value = user

        with pytest.raises(UserLockedError):
            await auth_service.login("alice", "correct-password")

        # ロック中はパスワード検証や失敗カウント更新を行わない
        assert user.failed_login_count == constants.LOGIN_FAILURE_LIMIT
        user_repository.flush.assert_not_awaited()

    async def test_login_lock_exactly_at_now_is_not_treated_as_locked(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        """locked_until == now（境界）はロック中として扱わない（`>`判定のため）。"""
        now = datetime.now(UTC)
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=constants.LOGIN_FAILURE_LIMIT,
            locked_until=now,
        )
        user_repository.get_by_login_id.return_value = user

        result = await auth_service.login("alice", "correct-password")

        assert result is user
        assert user.locked_until is None

    async def test_login_after_lock_expiry_resets_state_and_succeeds(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=constants.LOGIN_FAILURE_LIMIT,
            locked_until=datetime.now(UTC) - timedelta(minutes=1),
        )
        user_repository.get_by_login_id.return_value = user

        result = await auth_service.login("alice", "correct-password")

        assert result is user
        assert user.failed_login_count == 0
        assert user.locked_until is None

    async def test_login_after_lock_expiry_with_wrong_password_counts_as_first_failure(
        self, auth_service: AuthService, user_repository: AsyncMock
    ) -> None:
        user = make_user(
            password_hash=_password_hasher.hash("correct-password"),
            failed_login_count=constants.LOGIN_FAILURE_LIMIT,
            locked_until=datetime.now(UTC) - timedelta(minutes=1),
        )
        user_repository.get_by_login_id.return_value = user

        with pytest.raises(UnauthorizedError):
            await auth_service.login("alice", "wrong-password")

        # ロック解除後の1回目の失敗として扱われ、再ロックはされない
        assert user.failed_login_count == 1
        assert user.locked_until is None

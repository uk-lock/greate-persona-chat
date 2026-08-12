"""`app/api/dependencies.py`のうち、DBに依存しないJWT関連ロジックの単体テスト。

`get_current_user`等のDB（`UserRepository`）に依存する関数はIT側で担保するため対象外とする。
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.api import dependencies
from app.api.dependencies import (
    _decode_user_id,
    create_access_token,
    get_user_id_for_rate_limit,
)
from app.config import constants, settings
from app.services.exceptions import UnauthorizedError
from tests.factories import make_user


class _FakeRequest:
    """`get_user_id_for_rate_limit`が参照する`request.cookies`のみを持つダミー。"""

    def __init__(self, token: str | None) -> None:
        self.cookies: dict[str, str] = (
            {constants.AUTH_COOKIE_NAME: token} if token is not None else {}
        )


def _encode(payload: dict[str, object]) -> str:
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=constants.JWT_ALGORITHM
    )


class TestCreateAccessToken:
    def test_encodes_user_id_and_expiry(self) -> None:
        user = make_user(id=42)

        before = datetime.now(UTC)
        token = create_access_token(user)
        after = datetime.now(UTC)

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[constants.JWT_ALGORITHM]
        )
        assert payload["sub"] == "42"
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        # JWTのexpは秒単位（小数点以下切り捨て）でエンコードされるため、
        # 切り捨て分（1秒未満）を許容してtimedeltaの境界と比較する。
        assert (
            before + timedelta(hours=constants.JWT_EXPIRE_HOURS) - timedelta(seconds=1)
            <= exp
        )
        assert exp <= after + timedelta(hours=constants.JWT_EXPIRE_HOURS)


class TestDecodeUserId:
    def test_valid_token_returns_user_id(self) -> None:
        token = create_access_token(make_user(id=7))

        assert _decode_user_id(token) == 7

    def test_malformed_token_raises_unauthorized(self) -> None:
        with pytest.raises(UnauthorizedError):
            _decode_user_id("not-a-jwt")

    def test_expired_token_raises_unauthorized(self) -> None:
        token = _encode(
            {
                "sub": "1",
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "exp": datetime.now(UTC) - timedelta(hours=1),
            }
        )

        with pytest.raises(UnauthorizedError):
            _decode_user_id(token)

    def test_missing_sub_raises_unauthorized(self) -> None:
        token = _encode(
            {"iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(hours=1)}
        )

        with pytest.raises(UnauthorizedError):
            _decode_user_id(token)

    def test_non_integer_sub_raises_unauthorized(self) -> None:
        token = _encode(
            {
                "sub": "not-an-int",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(hours=1),
            }
        )

        with pytest.raises(UnauthorizedError):
            _decode_user_id(token)


class TestGetUserIdForRateLimit:
    def test_no_cookie_falls_back_to_remote_address(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            dependencies, "get_remote_address", lambda request: "1.2.3.4"
        )

        result = get_user_id_for_rate_limit(_FakeRequest(None))  # type: ignore[arg-type]

        assert result == "1.2.3.4"

    def test_valid_token_returns_user_id_as_string(self) -> None:
        token = create_access_token(make_user(id=9))

        result = get_user_id_for_rate_limit(_FakeRequest(token))  # type: ignore[arg-type]

        assert result == "9"

    def test_invalid_token_falls_back_to_remote_address(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            dependencies, "get_remote_address", lambda request: "5.6.7.8"
        )

        result = get_user_id_for_rate_limit(_FakeRequest("not-a-jwt"))  # type: ignore[arg-type]

        assert result == "5.6.7.8"

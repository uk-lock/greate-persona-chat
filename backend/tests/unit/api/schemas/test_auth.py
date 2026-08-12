"""`app/api/schemas/auth.py`の単体テスト。

`SignupRequest`のバリデータ（login_idの文字種チェック）を検証する。
"""

import pytest
from pydantic import ValidationError

from app.api.schemas.auth import SignupRequest


class TestValidateLoginIdCharset:
    @pytest.mark.parametrize("login_id", ["alice", "Alice123", "12345"])
    def test_alphanumeric_login_id_is_valid(self, login_id: str) -> None:
        SignupRequest.model_validate({"login_id": login_id, "password": "password123"})

    @pytest.mark.parametrize(
        "login_id",
        [
            "",
            "alice-123",
            "alice_123",
            "alice 123",
            "あいす",
            "alice@example.com",
        ],
    )
    def test_non_alphanumeric_login_id_is_invalid(self, login_id: str) -> None:
        with pytest.raises(ValidationError):
            SignupRequest.model_validate(
                {"login_id": login_id, "password": "password123"}
            )

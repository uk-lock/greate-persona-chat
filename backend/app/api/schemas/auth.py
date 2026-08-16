"""認証（サインアップ・ログイン）関連のリクエスト/レスポンススキーマ。"""

import re

from pydantic import BaseModel, Field, field_validator

_LOGIN_ID_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
"""半角英数字のみを許容する（db.md m_user.login_id参照）。"""


class SignupRequest(BaseModel):
    """サインアップリクエスト。"""

    login_id: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("login_id")
    @classmethod
    def validate_login_id_charset(cls, value: str) -> str:
        """login_idが半角英数字のみで構成されていることを検証する。"""
        if not value or not _LOGIN_ID_PATTERN.fullmatch(value):
            raise ValueError("ログインIDは半角英数字で入力してください")
        return value


class LoginRequest(BaseModel):
    """ログインリクエスト。"""

    login_id: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=255)


class AuthResponse(BaseModel):
    """サインアップ・ログイン成功時のレスポンス。

    認証の実体はHttpOnly CookieへのJWT設定であるため、レスポンスボディは
    最小限とする（S00-login.md・S06-signup.md参照）。
    """

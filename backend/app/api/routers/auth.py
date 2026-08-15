"""認証（サインアップ・ログイン・ログアウト）関連のルーター。"""

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import create_access_token, get_auth_service
from app.api.rate_limit import limiter
from app.api.schemas.auth import AuthResponse, LoginRequest, SignupRequest
from app.config import constants, settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """JWTをHttpOnly Cookieとして設定する（backend-python.md 15節）。"""
    response.set_cookie(
        key=constants.AUTH_COOKIE_NAME,
        value=token,
        max_age=constants.JWT_EXPIRE_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router.post("/signup", status_code=201)
@limiter.limit(f"{settings.rate_limit_signup_per_hour}/hour")
async def signup(
    request: Request,
    body: SignupRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """自己登録（サインアップ）し、成功時は自動的にログイン状態にする。

    Raises:
        ForbiddenError: サインアップ機能が無効化されている場合（403に変換される）。
        ConflictError: login_idが既に使用されている場合（409に変換される）。
    """
    user = await auth_service.signup(body.login_id, body.password)
    _set_auth_cookie(response, create_access_token(user))
    return AuthResponse()


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """ログインID・パスワードを検証し、JWTをCookieに設定する。

    Raises:
        UnauthorizedError: 認証情報が正しくない場合（401に変換される）。
        UserLockedError: 連続失敗によりロック中の場合（423に変換される）。
    """
    user = await auth_service.login(body.login_id, body.password)
    _set_auth_cookie(response, create_access_token(user))
    return AuthResponse()


@router.post("/logout")
async def logout(response: Response) -> AuthResponse:
    """Cookieに設定されたJWTを破棄する。"""
    response.delete_cookie(key=constants.AUTH_COOKIE_NAME)
    return AuthResponse()

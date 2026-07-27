"""slowapiによるレート制限の共通設定（backend-python.md 16節）。"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
"""既定のキー関数はIPアドレス（未認証エンドポイント用）。

認証必須エンドポイントでユーザー単位のカウントが必要な場合は、
`@limiter.limit(..., key_func=get_user_id_for_rate_limit)`のように個別に指定する。
"""

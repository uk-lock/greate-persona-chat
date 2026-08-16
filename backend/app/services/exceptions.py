"""サービス層の業務例外。

HTTPステータスコードは持たない（API層の対応表でHTTPステータスコードへ変換する）。
"""


class AppError(Exception):
    """全ての業務例外の基底クラス。"""


class NotFoundError(AppError):
    """対象のリソースが存在しない、または論理削除済みの場合の例外。"""


class ConflictError(AppError):
    """一意制約等、既存データと矛盾する場合の例外。"""


class UnauthorizedError(AppError):
    """認証情報（ログインID・パスワード等）が正しくない場合の例外。"""


class UserLockedError(AppError):
    """ログイン連続失敗によりユーザがロックされている場合の例外。"""


class ForbiddenError(AppError):
    """認可されていない操作（他ユーザーのリソースへの操作等）を試みた場合の例外。"""


class ValidationError(AppError):
    """DBアクセスを伴う、または文脈依存のためスキーマ層では表現できないバリデーション違反の例外。"""


class ExternalServiceError(AppError):
    """外部API（LLM等）呼び出しが、リトライを使い切っても失敗した場合の例外。"""

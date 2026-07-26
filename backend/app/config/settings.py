"""環境変数から読み込むアプリケーション設定。"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数から読み込む設定値。

    未設定の環境変数がある場合は、アプリ起動時にバリデーションエラーとする
    （デフォルト値による意図しないフォールバックを避けるため）。
    DB接続情報・JWT秘密鍵等は、それらを使う機能の実装時に追加する。
    """

    signup_enabled: bool
    """セルフサインアップ機能の有効/無効フラグ。"""

    database_url: str
    """DB接続URL（例：postgresql://user:pass@host:5432/dbname）。

    asyncpg用のドライバ指定（postgresql+asyncpg://）への読み替えはengine生成側で行う。
    """

    jwt_secret_key: str
    """JWT署名用の秘密鍵。"""


# signup_enabledはデフォルト値を持たず実行時に環境変数から供給されるが、
# mypyはBaseSettingsのこの挙動を認識できず必須引数として扱うため無視する
settings = Settings()  # type: ignore[call-arg]

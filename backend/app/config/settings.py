"""環境変数から読み込むアプリケーション設定。"""

from pydantic_settings import BaseSettings
from sqlalchemy.engine import make_url


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

    reply_model: str
    """ペルソナ応答生成に使うモデル。`langchain`の`init_chat_model`に渡す
    `プロバイダ名:モデル名`形式の文字列（例：`openai:gpt-5-mini`）。"""

    selection_model: str
    """応答ペルソナ選択（連鎖発言の継続判断を含む）に使うモデル。形式はreply_modelと同じ。"""

    title_model: str
    """チャットタイトル自動生成に使うモデル。形式はreply_modelと同じ。"""

    rate_limit_signup_per_hour: int
    """サインアップAPI（POST /auth/signup）のレート制限（1時間あたりの上限回数、
    IPアドレス単位）。本番/開発では小さい値（例：3）を想定するが、IT・E2Eでは
    テストクライアント・フロントエンドコンテナ経由で全リクエストが同一IPに見えるため、
    より大きい値に環境ごと上書きする（IT_RATE_LIMIT_SIGNUP_PER_HOUR・
    E2E_RATE_LIMIT_SIGNUP_PER_HOUR。docs/testing.md参照）。"""

    openai_api_key: str | None = None
    """OpenAI APIキー。reply_model等でprovider=openaiを指定した場合に必要。

    利用するプロバイダごとに対応するAPIキーのフィールドをここへ追加していく。
    全プロバイダ分を先回りして定義はしない（YAGNI。backend-python.md 10節と同じ考え方）。
    """

    deepseek_api_key: str | None = None
    """DeepSeek APIキー。reply_model等でprovider=deepseekを指定した場合に必要。"""


# signup_enabledはデフォルト値を持たず実行時に環境変数から供給されるが、
# mypyはBaseSettingsのこの挙動を認識できず必須引数として扱うため無視する
settings = Settings()  # type: ignore[call-arg]


def asyncpg_database_url() -> str:
    """`settings.database_url`をasyncpgドライバ向けに正規化したURL文字列を返す。

    アプリ本体（app/api/dependencies.py）・Alembic（migrations/env.py）・ITのDB fixture
    （tests/integration/conftest.py）が同じ変換ロジックを共有するための派生値（5節）。

    - ドライバ指定を`postgresql+asyncpg`へ読み替える。
    - Neon（IT・E2E・本番）の接続文字列は`channel_binding`・`sslmode`クエリパラメータを
      含むが、いずれもlibpq系クライアント向けのパラメータでasyncpgが認識せず接続エラーに
      なるため、これらが含まれる場合のみ除去し、代わりにasyncpgが認識する`ssl=require`を
      付与してTLS接続自体は維持する（asyncpgは`ssl`パラメータの値としてlibpq形式の文字列を
      受け付ける。`true`等の真偽値文字列は不可）。
    - ローカル開発用DB（`db`サービス、`postgres:17-alpine`）はSSLを有効化しておらず、
      接続文字列にも`sslmode`等は含まれないため、この分岐には入らない
      （`ssl=require`を無条件に付けるとSSL未対応のdbサービス相手に接続が拒否される）。
    """
    url = make_url(settings.database_url).set(drivername="postgresql+asyncpg")
    if {"channel_binding", "sslmode"} & set(url.query):
        url = url.difference_update_query(
            ["channel_binding", "sslmode"]
        ).update_query_dict({"ssl": "require"})
    return url.render_as_string(hide_password=False)

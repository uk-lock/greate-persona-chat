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
    - `channel_binding`・`sslmode`クエリパラメータを除去する（Neonの接続文字列に含まれるが、
      いずれもlibpq系クライアント向けのパラメータでasyncpgが認識せず接続エラーになるため）。
    - 代わりにasyncpgが認識する`ssl=require`を付与し、TLS接続自体は維持する
      （asyncpgは`ssl`パラメータの値としてlibpq形式の文字列を受け付ける。`true`等の
      真偽値文字列は不可）。
    """
    return (
        make_url(settings.database_url)
        .set(drivername="postgresql+asyncpg")
        .difference_update_query(["channel_binding", "sslmode"])
        .update_query_dict({"ssl": "require"})
        .render_as_string(hide_password=False)
    )

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

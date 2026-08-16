"""pytest全体（unit・integration共通）で読み込まれる設定。

`app.config.settings`（`Settings`）は環境変数から必須項目を読み込み、
未設定の場合はimport時点でバリデーションエラーになる。UTはDB・外部サービスへ
実際に接続しないため値そのものに意味はなく、型を満たすダミー値であれば十分。
docker compose環境等で既に環境変数が設定されている場合はそちらを優先する
（`setdefault`のため上書きしない）。
"""

import os

os.environ.setdefault("SIGNUP_ENABLED", "true")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("REPLY_MODEL", "openai:gpt-4o-mini")
os.environ.setdefault("SELECTION_MODEL", "openai:gpt-4o-mini")
os.environ.setdefault("TITLE_MODEL", "openai:gpt-4o-mini")
os.environ.setdefault("RATE_LIMIT_SIGNUP_PER_HOUR", "3")

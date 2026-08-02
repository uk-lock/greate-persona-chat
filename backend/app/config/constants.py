"""環境変数以外の、ドメイン上意味を持つ固定値。"""

LOGIN_FAILURE_LIMIT = 10
"""ログイン連続失敗の許容回数。これに達するとロックする。"""

LOGIN_LOCK_DURATION_MINUTES = 15
"""ログインロックの継続時間（分）。"""

DEFAULT_CHAT_TITLE = "新規チャット"
"""チャット作成時点でのタイトル初期値（会話内容をもとにしたLLMによる自動生成前）。"""

JWT_ALGORITHM = "HS256"
"""JWTの署名アルゴリズム。"""

JWT_EXPIRE_HOURS = 24
"""JWTの有効期限（時間）。"""

AUTH_COOKIE_NAME = "access_token"
"""JWTを格納するCookie名。"""

USER_MESSAGE_MAX_LENGTH = 500
"""USER_PARTICIPATEDモードでのユーザー発言本文の最大文字数。"""

CHAT_PERSONA_MIN_COUNT = 1
"""チャット作成時に選択可能なペルソナ数の下限。"""

CHAT_PERSONA_MAX_COUNT = 5
"""チャット作成時に選択可能なペルソナ数の上限。"""

PERSONA_ONLY_MAX_TURNS_PER_REQUEST = 50
"""PERSONA_ONLYモードの自動進行1コネクションあたりの最大ターン数（安全弁）。

仕様上は`stop`が呼ばれるまで無制限に継続するが、コネクションが
張られっぱなしになるリスク・LLM利用料の暴走を避けるための上限。
"""

USER_PARTICIPATED_CHAIN_MAX_TURNS = 5
"""USER_PARTICIPATEDモードでの連鎖発言（1回のユーザー発言に対する連続ペルソナ応答）の
最大ターン数（安全弁。api.md「連鎖回数の上限を設ける」に対応）。
"""

LLM_HISTORY_MAX_MESSAGES = 30
"""ペルソナ応答生成・応答ペルソナ選択のプロンプトに含める会話履歴の最大件数。

LLM利用料を抑えるため、直近この件数分のみをコンテキストとして渡す。
"""

RATE_LIMIT_MESSAGE_PER_MINUTE = 10
"""メッセージ送信APIのレート制限（1分あたりの回数、ユーザー単位）。"""

RATE_LIMIT_MESSAGE_PER_DAY = 50
"""メッセージ送信APIのレート制限（1日あたりの回数、ユーザー単位）。"""

RATE_LIMIT_SIGNUP_PER_HOUR = 3
"""サインアップAPIのレート制限（1時間あたりの回数、IPアドレス単位）。"""

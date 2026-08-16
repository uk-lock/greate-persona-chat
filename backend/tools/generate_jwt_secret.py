"""JWT_SECRET_KEY用の秘密鍵を生成し、標準出力に表示するツール。

使い方:
    python backend/tool/generate_jwt_secret.py
"""

import secrets


def generate_jwt_secret_key() -> str:
    """JWT署名（HS256）用に十分な長さを持つランダムな秘密鍵を生成する。

    Returns:
        URL-safeなランダム文字列（32バイトの乱数由来。PyJWTがHS256に推奨する
        最低長を満たす）。
    """
    return secrets.token_urlsafe(32)


if __name__ == "__main__":
    print(generate_jwt_secret_key())

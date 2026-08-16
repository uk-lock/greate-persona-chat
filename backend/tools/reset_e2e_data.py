"""E2Eテスト用DBリセットツール（TRUNCATE + 初期データ再投入）。

E2Eテスト（Playwright）はブラウザ→UI→API→DBという実際のHTTPフローを通すため、ITの
`tests/integration/`のようにSAVEPOINTでラップしてロールバックする方式が使えない
（サインアップやチャット送信の内容が実コミットとしてDBに残る）。

そのため、E2E実行前にこのツールで毎回テーブルを空にし、既存の初期データ投入ツール
（`tools.insert_init_data`）で初期ユーザ・ペルソナを再投入して既知のクリーンな状態に戻す
（docs/testing.md 5節参照）。

使い方（`compose.e2e.yml`経由でNeonのE2E専用ブランチに対して実行する想定）:
    docker compose -f compose.yml -f compose.e2e.yml run --rm backend python -m tools.reset_e2e_data

TRUNCATEは不可逆な破壊的操作のため、誤って想定外のDB（開発DB・本番DB等）に対して実行
してしまう事故を避ける簡易的な安全弁として、`.env`の`E2E_RESET_CONFIRM`（bool、既定false）が
trueでない場合は何もせず終了する。`compose.e2e.yml`のbackendサービスにのみ渡しているため、
dev/it/prod用のcomposeオーバーレイ経由で誤ってこのツールを実行してもtrueにはならない。
"""

import asyncio

from pydantic_settings import BaseSettings
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config.settings import asyncpg_database_url
from tools.insert_init_data import insert_init_persona, insert_init_user


class _ResetConfirmSettings(BaseSettings):
    """`E2E_RESET_CONFIRM`の読み込み専用設定（既存のSettingsと同じpydantic-settings流儀）。

    `app.config.settings.Settings`本体には持たせない。E2Eリセットツール固有の安全弁であり、
    アプリ本体・Alembic・ITが参照する設定とは関心事が異なるため。
    """

    e2e_reset_confirm: bool = False


# CASCADEで依存テーブルも合わせて空になるが、対象を明示するため全テーブルを列挙する
_TABLES_TO_TRUNCATE = (
    "t_chat_message",
    "t_chat_persona",
    "t_chat",
    "m_persona",
    "m_user",
)


async def truncate_all_tables() -> None:
    """アプリの全テーブルをTRUNCATEする（RESTART IDENTITY CASCADE）。"""
    engine = create_async_engine(asyncpg_database_url())
    try:
        async with engine.begin() as conn:
            table_list = ", ".join(_TABLES_TO_TRUNCATE)
            await conn.execute(
                text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
            )
        print(f"TRUNCATEしました: {table_list}")
    finally:
        await engine.dispose()


async def reset_e2e_data() -> None:
    """E2E用DBをTRUNCATEし、初期ユーザ・ペルソナを再投入する。"""
    # 接続文字列そのものはパスワードを含むため出力しない。誤接続に気づけるよう
    # ホスト名・DB名（マスクしても問題ない情報）だけ表示する。
    made_url = make_url(asyncpg_database_url())
    print(f"接続先: host={made_url.host} database={made_url.database}")

    if not _ResetConfirmSettings().e2e_reset_confirm:
        print(
            ".envのE2E_RESET_CONFIRMがtrueではないため、何もせず終了します"
            "（誤実行防止の安全弁。TRUNCATEは不可逆な操作です）。"
        )
        return

    await truncate_all_tables()

    engine = create_async_engine(asyncpg_database_url())
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            await insert_init_user(session)
            await insert_init_persona(session)
    finally:
        await engine.dispose()

    print("初期データの再投入が完了しました。")


if __name__ == "__main__":
    asyncio.run(reset_e2e_data())

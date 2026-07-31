"""Alembicのマイグレーション実行環境を組み立てるモジュール。

接続先はalembic.iniのsqlalchemy.urlではなくapp.config.settings（環境変数DATABASE_URL）
から取得し、アプリ本体（app/api/dependencies.py）と同じくasyncpgドライバへ読み替える。
マイグレーションとアプリでドライバがずれると、方言差による差分検出の誤りにつながるため。
"""

import asyncio
from logging.config import fileConfig

import sqlalchemy
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

# app.modelsパッケージのimportにより、配下の全モデル（user/persona/chat/
# chat_persona/chat_message）がBase.metadataへ登録される。
# app/models/__init__.pyが全モデルをre-exportしている点に依存しているため、
# ここをapp.models.baseからの直接importに変更してはいけない。
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata: sqlalchemy.MetaData = Base.metadata

DATABASE_URL: str = str(
    make_url(settings.database_url).set(drivername="postgresql+asyncpg")
)


def run_migrations_offline() -> None:
    """オフラインモード（DBへ接続せずSQLを出力するモード）でマイグレーションを実行する。

    `alembic upgrade head --sql` のように、適用せずSQLだけ確認したい場合に使われる。
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """マイグレーション本体を実行する。

    Args:
        connection: run_syncによって同期APIとして扱えるようにしたDBコネクション。
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期エンジンでDBへ接続し、マイグレーションを実行する。

    Alembicのマイグレーション処理自体は同期APIのため、connection.run_syncを介して呼び出す。
    """
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """オンラインモード（実DBへ接続して適用するモード）でマイグレーションを実行する。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# greate-persona-chat

ペルソナを設定してチャットできるアプリ。

## 技術スタック

- **フロントエンド**: Next.js 16 / React 19 / TypeScript / Tailwind CSS
- **バックエンド**: FastAPI / SQLAlchemy / Python 3.12
- **DB**: PostgreSQL 17（スキーマ管理はAlembic）

## アプリ起動手順（開発）
```bash
docker compose -f compose.yml -f compose.dev.yml up -d
```

## DBマイグレーション

スキーマ変更はAlembicで管理する。コンテナ起動時の自動適用はせず、手動で適用する。

```bash
docker compose exec backend alembic upgrade head
```

新規マイグレーションの作り方を含む詳細は [docs/migration.md](./docs/migration.md) を参照。

## テスト

```bash
# Backend UT・lint・型チェック
cd backend && pytest && ruff check . && ruff format --check . && mypy app

# Frontend UT・lint・型チェック・format確認
cd frontend && npm test && npm run lint && npm run typecheck && npm run format:check
```

git push時にBackend／FrontendのUT・lint・format確認・型チェックを自動実行するpre-pushフック（Husky）を用意している。
frontend devcontainerを一度でも作成すれば自動セットアップされる（`postCreateCommand`）。
backend devcontainerのみ使う場合は、npmが使える場所で初回に1回だけ実行する：

```bash
npm install
```

IT（結合テスト）はdevcontainerを使わず、Neonのテストブランチ接続情報（`.env`の`IT_DATABASE_URL`等）を
用意した上で以下で実行する（マイグレーション適用は冪等なため毎回実行して問題ない）：

```bash
docker compose -f compose.yml -f compose.it.yml run --rm backend sh -c "alembic upgrade head && pytest tests/integration"
```

コマンド一覧・ITの詳細・pre-pushフックの詳細は
[docs/testing.md](./docs/testing.md) を参照。

## 初期データ投入

ペルソナ作成用の管理画面はMVP対象外（DB直接投入前提、[docs/screen-list.md](./docs/screen-list.md) 4節）のため、
初期データは`backend/tools/`配下のツールでDBへ直接投入する。

```bash
# 事前にbackend/data/init_user.json（login_id・password）とbackend/data/init_persona.json（ペルソナ一覧）を用意する
docker compose exec backend python -m tools.insert_init_data
```

初期ユーザ・ペルソナをまとめて投入する。いずれも同一データを指すレコードが既に存在する場合は何もしない（べき等）。

`backend/data/`は投入用の一時的な作業ファイル置き場のためgit管理対象外（`.gitignore`）とする。
投入後はDB側が正であり、`init_user.json`・`init_persona.json`は各自のローカルで用意する。
# 開発者向けセットアップ

このリポジトリをクローンして実際にセットアップ・開発する人向けのドキュメント。
（プロダクトとしての紹介は[README.md](../README.md)を参照）

## 技術スタック

- **フロントエンド**: Next.js 16 / React 19 / TypeScript / Tailwind CSS
- **バックエンド**: FastAPI / SQLAlchemy / Python 3.12
- **DB**: PostgreSQL 17（スキーマ管理はAlembic）

## 開発コマンド（Makefile）

開発環境の起動・テスト実行はMakefileにまとめている。`make help`で一覧を確認できる。

| コマンド | 内容 |
|---|---|
| `make up-dev` | 開発環境を起動 |
| `make down-dev` | 開発環境を停止 |
| `make migrate-dev` | 開発環境DBへマイグレーションを適用 |
| `make ut-backend` | Backend UT・lint・format・型チェック |
| `make ut-frontend` | Frontend UT・lint・型チェック・format確認 |
| `make ut` | Backend/FrontendのUTを両方実行 |
| `make it` | 結合テスト（IT）を実行 |
| `make e2e` | E2Eテスト（Playwright）を通しで実行 |

各コマンドの中身（生の`docker compose`コマンド等）は以下の各節を参照。

## アプリ起動手順（開発）

```bash
docker compose -f compose.yml -f compose.dev.yml up -d
```

## DBマイグレーション

スキーマ変更はAlembicで管理する。コンテナ起動時の自動適用はせず、手動で適用する。

```bash
docker compose exec backend alembic upgrade head
```

新規マイグレーションの作り方を含む詳細は [docs/migration.md](./migration.md) を参照。

## テスト

```bash
# Backend UT・lint・型チェック
cd backend && pytest && ruff check . && ruff format --check . && mypy app

# Frontend UT・lint・型チェック・format確認
cd frontend && npm test && npm run lint && npm run typecheck && npm run format:check
```

git push時にBackend／FrontendのUT・lint・format確認・型チェックを自動実行するpre-pushフック（Husky）を用意している。
frontend devcontainerを一度でも作成すれば自動セットアップされる（`postCreateCommand`）。

git commit時には、gitleaksでステージされた変更内のシークレット漏洩を検知するpre-commitフック
（Husky）も用意している。gitleaksはローカルPCでは各自事前install、backend/frontendの
devcontainerでは`Dockerfile.dev`内で自動installされる。

ITにおけるデータベースはPostgresのcontainerを使わず、Neonのテストブランチを用いる。
この際、接続情報（`.env`の`IT_DATABASE_URL`等）を用意した上で以下で実行する（マイグレーション適用は冪等なため毎回実行して問題ない）：

```bash
docker compose -f compose.yml -f compose.it.yml run --rm backend sh -c "alembic upgrade head && pytest tests/integration"
```

E2E（Playwright）はbackend・frontendともにDockerfile.prod相当でビルドし、Neonの
E2E専用ブランチ（IT用とは別ブランチ、`.env`の`E2E_DATABASE_URL`等）に対して実行する：

```bash
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend alembic upgrade head
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend python -m tools.reset_e2e_data
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e up -d --build backend frontend
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm --build e2e
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e down
```

コマンド一覧・IT／E2Eの詳細・pre-pushフックの詳細は
[docs/testing.md](./testing.md) を参照。

Claude CodeからブラウザをMCP経由で直接操作したい場合（frontend devContainer限定）は
[docs/testing.md 6節](./testing.md#6-playwright-mcpclaude-code用) を参照。

## 初期データ投入

ペルソナ作成用の管理画面はMVP対象外（DB直接投入前提、[docs/screen-list.md](./screen-list.md) 4節）のため、
初期データは`backend/tools/`配下のツールでDBへ直接投入する。

```bash
# 事前にbackend/data/init_user.json（login_id・password）とbackend/data/init_persona.json（ペルソナ一覧）を用意する
docker compose exec backend python -m tools.insert_init_data
```

初期ユーザ・ペルソナをまとめて投入する。いずれも同一データを指すレコードが既に存在する場合は何もしない（べき等）。

`backend/data/`は投入用の一時的な作業ファイル置き場のためgit管理対象外（`.gitignore`）とする。
投入後はDB側が正であり、`init_user.json`・`init_persona.json`は各自のローカルで用意する。

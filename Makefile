.DEFAULT_GOAL := help

.PHONY: help up-dev down-dev migrate-dev ut-backend ut-frontend ut it e2e

help: ## コマンド一覧を表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

up-dev: ## 開発環境を起動（backend/frontend/db）
	docker compose -f compose.yml -f compose.dev.yml up -d

down-dev: ## 開発環境を停止
	docker compose -f compose.yml -f compose.dev.yml down

# 事前に `make up-dev` で backend コンテナが起動している必要あり
migrate-dev: ## 開発環境DBへマイグレーションを適用
	docker compose exec backend alembic upgrade head

# backend devcontainer内（pytest/ruff/mypyが使える環境）での実行を想定
ut-backend: ## Backend UT・lint・format・型チェック
	cd backend && pytest && ruff check . && ruff format --check . && mypy app

# frontend devcontainer内（npm install済み）での実行を想定
ut-frontend: ## Frontend UT・lint・型チェック・format確認
	cd frontend && npm test && npm run lint && npm run typecheck && npm run format:check

ut: ut-backend ut-frontend ## Backend/Frontend のUTを両方実行

# .envにIT_DATABASE_URL等（Neonテストブランチ接続情報）が必要
it: ## 結合テスト(IT)を実行
	docker compose -f compose.yml -f compose.it.yml run --rm backend sh -c "alembic upgrade head && pytest tests/integration"

# .envにE2E_*変数（Neon E2E専用ブランチ接続情報）とE2E_RESET_CONFIRM=trueが必要
e2e: ## E2Eテスト(Playwright)を通しで実行（マイグレーション→データリセット→ビルド起動→テスト→後片付け）
	docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend alembic upgrade head
	docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend python -m tools.reset_e2e_data
	docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e up -d --build backend frontend
	docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm --build e2e
	docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e down

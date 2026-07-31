# greate-persona-chat

ペルソナを設定してチャットできるアプリ。

## 技術スタック

- **フロントエンド**: Next.js 16 / React 19 / TypeScript / Tailwind CSS
- **バックエンド**: FastAPI / SQLAlchemy / Python 3.12
- **DB**: PostgreSQL 17（スキーマ管理はAlembic）

## DBマイグレーション

スキーマ変更はAlembicで管理する。コンテナ起動時の自動適用はせず、手動で適用する。

```bash
docker compose exec backend alembic upgrade head
```

新規マイグレーションの作り方を含む詳細は [docs/migration.md](./docs/migration.md) を参照。
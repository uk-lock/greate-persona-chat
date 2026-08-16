# DBマイグレーション運用

バックエンドのDBスキーマは [Alembic](https://alembic.sqlalchemy.org/) で管理する。
手動SQLでのスキーマ変更は行わない。

---

## 1. 構成

```text
backend/
├── alembic.ini                  … Alembic設定。接続URLは持たない（env.pyが組み立てる）
└── migrations/
    ├── env.py                   … 実行環境。target_metadataとDB接続を定義
    ├── script.py.mako           … マイグレーションファイルの雛形
    └── versions/                … マイグレーションファイル本体
```

- 対象メタデータは `app/models/base.py` の `Base.metadata`。
- `env.py` は `app.models` パッケージをimportしており、`app/models/__init__.py` が全モデルを
  re-exportすることで配下の全テーブルが `Base.metadata` に登録される。
  **モデルを追加したら `app/models/__init__.py` への追記を忘れないこと**（追記しないと
  autogenerateがそのテーブルを検出できない）。
- 接続先は `alembic.ini` ではなく環境変数 `DATABASE_URL`（`app/config/settings.py`）から取得し、
  アプリ本体と同じ `postgresql+asyncpg` ドライバへ読み替える。秘匿情報をリポジトリに置かないため。

---

## 2. 適用方針

**マイグレーションはコンテナ起動時に自動適用せず、手動で実行する。**

理由：

- 自動適用にすると、コンテナが再起動するたびにスキーマ変更が意図せず走る。適用タイミングを
  開発者が把握できる方が、失敗時の切り分けが容易になる。
- backend・frontendの複数コンテナ構成で起動時適用を入れると、起動順とヘルスチェックの調整が
  必要になり、「小さく作る」「既存構成を壊さない」方針に反する。
- そのため `compose.yml` / `Dockerfile` の変更は行っていない。

自動適用が必要になった時点で、起動コマンドへの `alembic upgrade head` の前置を検討する。

---

## 3. コマンド

`alembic` は **`backend/` 直下をカレントディレクトリにして実行する**
（`alembic.ini` の `prepend_sys_path = .` がカレントディレクトリ基準のため）。

devContainer（backend）内で作業している場合：

```bash
cd /workspace/backend
```

ホストからdocker compose経由で実行する場合：

```bash
docker compose exec backend <以下のコマンド>
```

### 3.1 現在の状態を確認する

```bash
alembic current   # DBに適用済みのリビジョン
alembic heads     # マイグレーションファイル側の最新リビジョン
alembic history   # 履歴一覧
```

### 3.2 マイグレーションを適用する

```bash
alembic upgrade head
```

### 3.3 新しいマイグレーションを作る

モデル（`app/models/`）を変更したあと、差分から自動生成する。

```bash
alembic revision --autogenerate -m "変更内容の要約"
```

生成後は**必ず `migrations/versions/` のファイルを目視で確認する**。autogenerateは
以下を検出できない・誤検出することがあるため、必要に応じて手で修正する。

- テーブル名・カラム名の変更（削除＋追加として生成される）
- CHECK制約、一部のserver_defaultの差分
- データ移行（既存行の値の詰め替え）

確認後、適用前にSQLだけ見たい場合は次で確認できる（DBには接続するが変更は行わない）。

```bash
alembic upgrade head --sql
```

### 3.4 巻き戻す

```bash
alembic downgrade -1     # 1つ前へ
alembic downgrade base   # 全て巻き戻す（全テーブル削除）
```

---

## 4. ベースラインマイグレーション

初回リビジョン `a1f4c9d2e7b3`（baseline schema）が、現時点のモデル定義に対応する
全テーブル（`m_user` / `m_persona` / `t_chat` / `t_chat_persona` / `t_chat_message`）を作成する。

このプロジェクトはAlembic導入前にデータを投入していないため、既存データとの整合を考慮する必要は
なかった。まっさらなDBに対して `alembic upgrade head` を実行すれば現在のスキーマが再現できる。

---

## 5. lint・型チェックの扱い

`migrations/` 配下は自動生成コードを含むが、lint・formatの除外対象にはしない
（[coding/common.md](./coding/common.md) 1節の除外規定は追加していない）。
`ruff check` / `ruff format` / `mypy --strict` が通る状態を保つ。
autogenerateの出力がフォーマット違反になった場合は、`ruff format migrations/` をかけてから
コミットする。

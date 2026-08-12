# テスト運用

Backend・FrontendそれぞれのUT（単体テスト）構成・実行コマンド・git push時の自動実行について記載する。
テスト方針そのもの（何をモックし、何を実DBで検証するか）は
[coding/backend-python.md 6節](./coding/backend-python.md) を参照。

---

## 1. Backend

### 1.1 構成

```text
backend/
└── tests/
    ├── conftest.py       … 全体共通設定（Settingsに必要なダミー環境変数の設定）
    ├── factories.py      … テスト用モデル（User/Persona/Chat等）のビルダー関数
    ├── unit/              … UT本体（DB・外部LLM APIに依存しない）
    │   └── services/      … app/services/ をミラーリング
    │   └── llm/           … app/llm/ をミラーリング（retry・state・models・nodes）
    │   └── api/           … app/api/ をミラーリング（routers・schemas・dependencies・exception handlers）
    └── integration/       … 将来のIT用（今回はディレクトリのみ用意、未実装）
```

- `unit/`配下は`app/`のディレクトリ構造をそのままミラーリングする。対象を追加する際も
  迷わない配置にするため（[coding/backend-python.md 6節](./coding/backend-python.md)）。
- `integration/`は、実DB（Docker Compose上のテスト用DB）に対して行う結合テストの置き場として
  分離してある。今回のスコープでは未実装。
- リポジトリ・LLMグラフ・チャットモデルはすべてモック／スタブに置き換え、実DB・実LLM APIには
  一切接続しない。
- 非同期テストは`pytest-asyncio`（`asyncio_mode = "auto"`、`pyproject.toml`）で
  `async def test_...`をそのまま実行できるようにしている。
- `pythonpath = ["."]`（`pyproject.toml`）により、実行時のカレントディレクトリや起動方法に
  よらず`app`パッケージをimportできるようにしている。

### 1.2 コマンド

事前に依存パッケージをインストールする（backend devcontainer内、または`backend/`をカレント
ディレクトリにして実行）。

```bash
cd backend
pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt
```

Backend UTのみを実行する（既定で`tests/unit`のみが対象。実DB・外部サービスには接続しない）。

```bash
cd backend
pytest
```

カバレッジ付きで実行する場合：

```bash
pytest --cov=app --cov-report=term-missing
```

失敗したテストの詳細を確認する場合（`-v`で個別テスト名、`-x`で最初の失敗で停止）：

```bash
pytest -v
pytest -x
```

lint・format確認・型チェック（[coding/backend-python.md 7節](./coding/backend-python.md)、push前にも自動実行される）：

```bash
ruff check .
ruff format --check .
mypy app
```

`mypy`は`app`ディレクトリ全体（`app/__init__.py`・`app/api/__init__.py`を含む、通常のPythonパッケージ構成）を対象にする。特別なフラグは不要。

### 1.3 IT（結合テスト）の分離方針

`tests/integration/`は、Docker Compose上のテスト用DBに対して実際にクエリを行う結合テストの
置き場として用意してあるが、今回のスコープでは未実装（フォルダのみ）。

- UTとは明確にディレクトリを分離しているため、`pytest`（引数なし）はITを一切含まない
  （`pyproject.toml`の`testpaths = ["tests/unit"]`）。
- IT追加後は `pytest tests/integration` のように明示的にパスを指定して実行する想定。
- テスト用DBの起動方法・接続情報の組み立て方は、IT実装時に別途本ドキュメントへ追記する。

---

## 2. Frontend

### 2.1 コマンド

```bash
cd frontend
npm install
npm test
```

`npm test`は`vitest run`のエイリアス（`package.json`）。Vitest + Testing Library + jsdom構成で、
実DB・実APIには接続しない。

lint・型チェック・format確認（[coding/frontend-typescript-react.md 3節](./coding/frontend-typescript-react.md)、push前にも自動実行される）：

```bash
npm run lint          # eslint（eslint-config-next）
npm run typecheck     # tsc --noEmit
npm run format:check  # prettier --check .
```

整形を実際に適用する場合：

```bash
npm run format         # prettier --write .
```

### 2.2 Prettierについて

`frontend-typescript-react.md 3節`の確定方針に基づき、今回新たにPrettierを導入した
（`.prettierrc.json` / `.prettierignore`）。導入時点で未整形だった既存ファイルは
一括で`prettier --write .`を適用済み（挙動に影響しない空白・改行のみの変更）。
`*.md`・`public/`配下・`node_modules`等は対象外（`.prettierignore`）。

### 2.3 現状

既存テストは`frontend/tests/`配下に17ファイル。棚卸し・追加は別途対応する
（本ラウンドのスコープ外）。

---

## 3. Backend／Frontendをまとめて実行する

```bash
(cd backend && ruff check . && ruff format --check . && mypy app && pytest) && \
(cd frontend && npm run lint && npm run typecheck && npm run format:check && npm test)
```

git push時は後述のpre-pushフックが自動的に同等のチェックを行う。

---

## 4. git push時の自動実行（pre-push フック）

### 4.1 採用方式

`docs/coding/common.md 10節`・`backend-python.md 7節`・`frontend-typescript-react.md 3節`で
「push前（pre-push、Husky経由）にBackend・Frontendともlint・format・型チェックを自動実行する」
と既に確定しているため、同じHuskyの仕組みに相乗りする形でUT実行も追加した。

`.husky/pre-push`が実行する内容：

| 対象 | 内容 |
| --- | --- |
| Backend | `ruff check .` → `ruff format --check .` → `mypy app` → `pytest` |
| Frontend | `npm run lint`（eslint） → `npm run typecheck`（tsc --noEmit） → `npm run format:check`（prettier） → `npm test`（vitest） |

いずれか1つでも失敗した場合、残りのステップも実行したうえで（最後まで実行して失敗箇所をまとめて表示する）pushを中止する。

- リポジトリルートに、フック管理専用の最小限の`package.json`（`devDependencies`は`husky`のみ）を追加。
- `.husky/pre-push`（シェルスクリプト、リポジトリにコミット済み）が実体。
- セットアップは、**リポジトリルートで`npm install`を1回実行するだけ**
  （`package.json`の`prepare`スクリプトがHuskyのフックを自動的に有効化する）。
  clone直後の別の開発者でも同じ手順で再現できる。個人の`.git/hooks/`へ手作業でスクリプトを
  置く必要はない。

### 4.2 devcontainerが分かれている制約への対応

このリポジトリはBackend用・Frontend用でdevcontainerが分かれており、一方のコンテナには
他方のツールチェーン（`pytest`/`ruff`/`mypy` / `npm`）が存在しない。そのため`.husky/pre-push`は、
実行環境に存在する方のチェックだけを自動実行し、存在しない方は警告を表示してスキップする
（`command -v pytest` / `command -v npm`で検知）。

```text
backendコンテナからpush → Backend（ruff/mypy/pytest）のみ自動実行、Frontendは警告表示
frontendコンテナからpush → Frontend（eslint/tsc/prettier/vitest）のみ自動実行、Backendは警告表示
```

そのため、**1回のpushでBackend／Frontend両方のチェックが必ず実行されるとは限らない**
（両方のツールチェーンが揃った環境からpushした場合のみ両方実行される）。運用上は、
自分が変更したレイヤーと反対側のレイヤーに影響する変更をした場合、pushする前に反対側の
コンテナでも手動で該当コマンド（1.2節・2.1節）を実行することを推奨する。

より厳密に両方を強制したい場合は、`compose.dev.yml`にDocker socketをマウントして
`docker compose exec`経由で相手コンテナのテストを呼ぶ方式が考えられるが、既存のcompose設定に
影響するため今回は見送った（今後の課題）。

### 4.3 セットアップ手順

**frontend devcontainerを一度でも作成すれば自動セットアップされる**
（`.devcontainer/frontend/devcontainer.json`の`postCreateCommand`が、コンテナ作成時に
リポジトリルートで`npm install`を実行する）。`.git`はbackend/frontend間で共有されるため、
以後はbackendコンテナから`git push`してもフックが有効になる。

backend devcontainerしか使わない開発者は、この自動化の対象外（backendコンテナにnpm自体が
無いため）。その場合は、npmが使える場所（ホスト等）で手動で1回だけ実行する。

```bash
# リポジトリルートで（npmが使える場所で）
npm install
```

以降、`git push`のたびに`.husky/pre-push`が自動実行される。緊急時は`git push --no-verify`で
スキップできる（通常運用では使わない）。

### 4.4 CIについて

pre-pushはローカルの`--no-verify`で回避可能なため、中央で強制力を持たせるにはCI
（例：GitHub Actionsでのpush/PR時のUT実行）が別途必要になる。今回のスコープには含めていない。

# テスト運用

Backend・FrontendそれぞれのUT（単体テスト）構成・実行コマンド・git push時の自動実行について記載する。
テスト方針そのもの（何をモックし、何を実DBで検証するか）は
[coding/backend-python.md 6節](./coding/backend-python.md) を参照。

以下で説明する各コマンドは、リポジトリルートのMakefileでもまとめて呼べる（`make help`で一覧表示）。

| 節 | 生コマンド | Makefile |
|---|---|---|
| 1.2 Backend UT・lint・型チェック | `cd backend && pytest && ruff check . && ruff format --check . && mypy app` | `make ut-backend` |
| 1.3 Backend IT | `docker compose -f compose.yml -f compose.it.yml run --rm backend sh -c "alembic upgrade head && pytest tests/integration"` | `make it` |
| 2.1 Frontend UT | `cd frontend && npm test` | `make ut-frontend`（lint・typecheck・format:check込み） |
| 5.5 E2E | 5コマンド一式 | `make e2e` |

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
    └── integration/       … IT本体（Neon上のテストブランチに実接続。1.3節参照）
```

- `unit/`配下は`app/`のディレクトリ構造をそのままミラーリングする。対象を追加する際も
  迷わない配置にするため（[coding/backend-python.md 6節](./coding/backend-python.md)）。
- `integration/`は、実DB（Neon上のテストブランチ）に対して行う結合テストの置き場として分離してある。
  詳細は1.3節を参照。
- `unit/`配下では、リポジトリ・LLMグラフ・チャットモデルはすべてモック／スタブに置き換え、
  実DB・実LLM APIには一切接続しない。
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

### 1.3 IT（結合テスト）

`tests/integration/`は、Neon上の専用テストブランチに対して実際にクエリを行う結合テストの置き場。
devcontainerは使わず、IT専用のオーバーレイ`compose.it.yml`（`compose.yml`にのみ重ねる）を使って
ホストから直接実行する。

- UTとは明確にディレクトリを分離しているため、`pytest`（引数なし）はITを一切含まない
  （`pyproject.toml`の`testpaths = ["tests/unit"]`）。
- 接続先は`IT_DATABASE_URL`（`.env`）を`compose.it.yml`が`DATABASE_URL`として渡す形。
  `compose.dev.yml`のローカルDBコンテナとは別経路。
- 各テストはトランザクションでラップし終了時にロールバックする
  （`tests/integration/conftest.py`）。共有のテストブランチを汚さない。
- 実行前に`alembic upgrade head`を挟んでいる。未適用のマイグレーションがあれば適用し、
  無ければ現在のリビジョンを確認するだけで何もしない（冪等）ため、毎回実行してよい。
  Neonのテストブランチにスキーマが無い状態でIT実行を忘れて失敗する、という事故を避けられる。

```bash
docker compose -f compose.yml -f compose.it.yml run --rm backend sh -c "alembic upgrade head && pytest tests/integration"
```

**LLM呼び出しのIT（`tests/integration/llm/`）**：実際のLLM APIに接続する唯一の例外
（[coding/backend-python.md 6節](./coding/backend-python.md)参照）。費用がかかるため、
上記の通常のIT実行には含まれない（`pyproject.toml`の`norecursedirs`で自動探索から除外）。
実行する場合はパスを明示的に指定する。

```bash
docker compose -f compose.yml -f compose.it.yml run --rm backend pytest tests/integration/llm
```

安価なモデルへの切り替えは`.env`の`IT_REPLY_MODEL`等で行う。失敗・タイムアウトのケースは
実際の生成が始まる前にエラーになるよう仕向けており、費用はごく小さい。

`tests/integration/api/test_auth.py`は1回のpytestプロセス内で複数回サインアップAPIを
呼ぶが、サインアップAPIのレート制限（`RATE_LIMIT_SIGNUP_PER_HOUR`、IPアドレス単位）は
テストクライアント越しだと全リクエストが同一IPに見えるため、本番と同じ値のままだと
IT自体が誤って引っかかりうる。`IT_RATE_LIMIT_SIGNUP_PER_HOUR`（`.env`）で緩めた値に
上書きする（E2Eも同じ理由で`E2E_RATE_LIMIT_SIGNUP_PER_HOUR`を使う。5.3節参照。
実装は`app/config/settings.py`の`rate_limit_signup_per_hour`）。

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

## 4. git push／commit時の自動実行（pre-push／pre-commit フック）

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
devcontainer内で実際に使える方のチェックだけを自動実行し、使えない方は警告を表示してスキップする。

devcontainer内かどうかは、`command -v pytest` / `command -v npm`だけでは判定しない
（host側にたまたまpytestやnodeがインストールされていると、devcontainer外からのpushでも
依存関係が揃わないまま誤って実行され、エラーになるため）。代わりに、
「Dockerコンテナ内である（`/.dockerenv`が存在する）」かつ「リポジトリルートが
`/workspace`である（`.devcontainer/*/devcontainer.json`の`workspaceFolder`と、
`compose.dev.yml`でのマウント先に一致）」の両方を満たす場合のみdevcontainer内と判定し、
そのうえで`command -v pytest` / `command -v npm`で対象を絞り込む。devcontainer内でないと
判定された場合はBackend・Frontendとも実行せず、警告のみ表示する。

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

### 4.5 git commit時の自動実行（pre-commit フック／gitleaks）

`.husky/pre-commit`が、[gitleaks](https://github.com/gitleaks/gitleaks)でステージされた変更
（`git diff --staged`相当）をスキャンし、APIキー等のシークレットらしき文字列を検知した場合は
commitを中止する（`gitleaks protect --staged`）。

pre-pushのツールチェーン確認（4.2節、devcontainer内かどうかで実行有無を出し分け・見つからない
場合は警告のみで続行）とは異なり、gitleaksは見つからない場合も**警告だけで済ませずcommitを中止する**。
シークレット検知はスキップされると意味がないチェックのため。

- ローカルPC：各自で事前installしておく（例: `brew install gitleaks`）。
- backend/frontendのdevcontainer：標準では入っていないため、`Dockerfile.dev`側で
  gitleaksのバイナリをGitHub Releasesから取得し同梱している
  （`ARG GITLEAKS_VERSION`で明示的にバージョン固定。更新時はbackend/frontend両方の
  `Dockerfile.dev`を揃えて更新する）。

誤検知した場合は、該当行に`gitleaks:allow`コメントを付与するか、リポジトリルートに
`.gitleaks.toml`を置いてallowlistを設定する（現状は未使用、default configのみで運用）。

`git commit --no-verify`で本フック自体をスキップできる（緊急時用。通常運用では使わない）。

---

## 5. E2E

Playwrightでbackend・frontendを通しでブラウザ操作し、UT／ITではカバーしない
画面をまたいだユーザー操作フローを検証する。

### 5.1 構成

```text
frontend/
├── Dockerfile.e2e         … Playwright runner専用イメージ（ビルド時にブラウザインストールまで完了）
├── playwright.config.ts   … testDir: "./e2e"、baseURLはE2E_BASE_URLから取得
└── e2e/                   … E2Eシナリオ本体（*.spec.ts）。frontend/tests/（Vitest）とは別ディレクトリ
    ├── support/helpers.ts       … 共通ヘルパー（signup/login/logout、衝突しないログインID生成）
    ├── happy-path.spec.ts       … サインアップ→ペルソナ→チャット送信までの一直線のhappy path
    ├── auth.spec.ts             … サインアップ／ログインのバリデーション・エラー・ロックアウト・認可
    ├── personas.spec.ts         … ペルソナ一覧の検索・詳細表示・存在しないIDへのアクセス
    ├── chat-creation.spec.ts    … 新規チャットのペルソナ選択・モード切替・履歴一覧・削除（LLM呼び出しなし）
    └── chat-messaging.spec.ts   … メッセージ送受信・PERSONA_ONLYの会話進行（LLM呼び出しを伴う）

backend/
└── tools/
    └── reset_e2e_data.py  … E2E実行前のDBリセット（5.4節）

compose.e2e.yml            … backend・frontend・e2eの3サービスからなるオーバーレイ
```

- `@playwright/test`は`frontend/package.json`のdevDependencies。本番イメージ（`Dockerfile.prod`）には含まれない。
- `frontend/vitest.config.mts`の`exclude`に`e2e/**`を追加し、`npm test`（Vitest）が
  `frontend/e2e/*.spec.ts`を誤って対象に含めないようにしている（Vitestのデフォルトの対象
  パターンは`*.spec.ts`にもマッチするため）。
- backend・frontendは常に`Dockerfile.prod`でビルドし、本番相当のイメージで動作確認する。
- `e2e`サービスは`network_mode: service:frontend`で`frontend`とネットワーク名前空間を共有し、
  `http://127.0.0.1:3000`でアクセスする（`networks:`とは併用不可のため指定していない）。
  host側のポート公開には依存しない（devcontainer経由でdocker socketをマウントする構成の
  ため、hostの公開ポートがdevcontainer内から見えるとは限らないことへの対応）。
  **`http://frontend:3000`ではなくloopbackアドレスにしているのは意図的**：backendが
  発行する認証Cookieには`Secure`属性が付いており、ブラウザは`http://localhost`・
  `127.0.0.1`だけを「安全な文脈」として特別扱いする（W3C secure context）。`frontend`の
  ようなDocker内部のホスト名でHTTPアクセスすると、ブラウザがCookie自体を保存せず、
  サインアップ・ログイン後も未ログイン扱いに戻ってしまう（本番のHTTPSでは起きない）。
  `network_mode: service:frontend`でネットワーク名前空間ごと共有すれば`localhost`・
  `127.0.0.1`が`frontend`コンテナを指すため、backend側のCookie設定（本番と同じ
  `Secure`属性）を一切変更せずに済む。`localhost`ではなく`127.0.0.1`を使っているのは、
  コンテナ内のDNS解決が`localhost`を先に`::1`（IPv6）へ解決してしまい、Next.jsサーバーが
  IPv4にしかbindしていないため接続できない事象が実際に発生したため（下記のHOSTNAME対応と
  併せて、`127.0.0.1`を使うことで確実に到達できるようにしている）。
- `frontend/Dockerfile.prod`のrunnerステージは`ENV HOSTNAME="0.0.0.0"`を明示的に設定して
  いる。Next.js standaloneサーバーは`HOSTNAME`環境変数のアドレスにのみbindするが、Dockerは
  全コンテナに自動でその固有ホスト名を`HOSTNAME`として設定してしまうため、何も指定しないと
  そのコンテナの個別IPにしかbindされず、`localhost`はおろか外部からも到達できなくなる
  （E2E導入時に発覚。Cloud Run等、コンテナランタイムが独自に`HOSTNAME`相当を設定してくる
  環境でも同様に起こりうる、Next.js standalone + Dockerの既知の落とし穴）。
- `frontend/Dockerfile.prod`は`next build`時に`API_BASE_URL`を要求する（`lib/config.ts`が
  ページデータ収集の過程で参照するため、ビルド時点で設定されていないとビルド自体が失敗する）。
  そのため`ARG API_BASE_URL`を追加し、`compose.prod.yml`・`compose.e2e.yml`の
  `build.args`から渡すようにした（E2E導入時に発覚した既存の不備で、E2Eに限らず
  `Dockerfile.prod`を使う全ての箇所に影響する修正）。E2Eではビルド時にしか使わない値のため
  `.env`の`E2E_API_BASE_URL`は実際に通信可能なURLである必要はなく、ダミー値でよい
  （実行時にfrontendが実際に使う`API_BASE_URL`は`compose.yml`側の値をそのまま継承する）。
  **Cloud Run等、composeを経由しないビルドパイプラインを使う場合はこの`build.args`は
  効かないため、そちらのビルド設定側で別途`API_BASE_URL`をbuild-argとして渡す必要がある**
  （渡し忘れると同じ理由でビルドが失敗する）。
- `next build`は本来`next/font/google`経由でフォントファイルをGoogle Fonts CDNから
  ビルド時に取得するが、日本語フォント（Zen Kaku Gothic New・Noto Sans JP）はGoogle側で
  文字コード範囲ごとに大量のファイル（700個超）に分割されているため取得数が桁違いに多く、
  ネットワークが少しでも不安定だと1つの失敗でビルド全体が落ちる、という壊れやすい状態
  だった（E2E導入時に発覚）。`network: host`等のネットワーク側の応急処置では解決しない
  環境があったため、**フォントファイルをリポジトリに同梱してビルド時のGoogle Fonts接続
  自体を無くす**方向で根本対応した:
  - `frontend/public/fonts/{zen-kaku-gothic-new,noto-sans-jp}/`: Google Fontsが配信して
    いるのと同じ粒度（文字コード範囲ごと）のwoff2ファイルをそのまま保存（合計約20MB）。
    ブラウザは実際に画面に出てくる文字範囲のファイルだけを読み込むため、実行時の挙動は
    Google Fonts利用時と変わらない。
  - `frontend/app/local-fonts.css`: 上記を指す`@font-face`定義（自動生成、手で編集しない）。
  - `app/layout.tsx`は`next/font/google`を使わず`./local-fonts.css`をimportするだけ。
    `--font-zen-kaku-gothic-new`・`--font-noto-sans-jp`（Tailwindの`font-display`・
    `font-body`が参照するCSS変数）は`app/globals.css`の`:root`で直接定義している。
  - これにより`compose.e2e.yml`・`compose.prod.yml`のどちらにも`network: host`は
    不要になった（一時的に追加していたが、この対応後に削除済み）。

### 5.2 Neonブランチ方針

IT用のテストブランチとは**別のE2E専用Neonブランチ**を使う。

ITは各テストをSAVEPOINTでラップし終了時にロールバックすることで「共有テストブランチを
汚さない」という前提が成り立っているが（1.3節）、E2Eはブラウザ→UI→API→DBという実際の
HTTPフローを通すため、サインアップやチャット送信などの操作が実コミットとしてDBに残る。
IT用ブランチと共有すると、E2Eの残留データ（重複ユーザー等）がITの一意制約テストなどを
壊すリスクがあるため、ブランチ自体を分離している。

### 5.3 `.env`キー

IT用の`IT_*`命名規則に倣い、以下を追加する（値はコミットしない）。

```text
E2E_DATABASE_URL       … E2E専用Neonブランチの接続文字列
E2E_SIGNUP_ENABLED
E2E_REPLY_MODEL        … 安価なモデルに切り替え可能（IT_REPLY_MODEL等と同じ考え方）
E2E_SELECTION_MODEL
E2E_TITLE_MODEL
E2E_RATE_LIMIT_SIGNUP_PER_HOUR … サインアップAPIのレート制限の上書き値。E2Eは
                          frontendコンテナ経由で全リクエストが同一IPに見えるため、
                          本番の既定値（3）のままだとテスト一式ですぐ上限に達する。
                          1000程度を推奨（1.3節参照）
E2E_RESET_CONFIRM      … bool（true/false）。5.4節参照。既定false
E2E_BACKEND_PORT        … 省略可。既定8100（devスタックの8000と衝突しないポート）
E2E_FRONTEND_PORT       … 省略可。既定3100（devスタックの3000と衝突しないポート）
E2E_API_BASE_URL       … frontendのDockerビルド時のみに使う値（5.1節参照）。実行時に
                          実際に通信するわけではないため、任意のダミー値でよい
```

### 5.4 データリセット（TRUNCATE + 初期データ再投入）

E2Eは実コミットが残るためITのロールバック方式が使えない。代わりに、実行前に
`backend/tools/reset_e2e_data.py`で全テーブルをTRUNCATEし、既存の初期データ投入ツール
（`tools.insert_init_data`、[README.md「初期データ投入」](../README.md)参照）を呼び出して
初期ユーザ・ペルソナを再投入することで、毎回既知のクリーンな状態に戻す（べき等ではなく
「必ず空にしてから入れ直す」方式）。

TRUNCATEは不可逆な操作のため、誤って別のDB（開発DB・本番DB等）に対して実行してしまう
事故を避ける簡易的な安全弁として、`.env`の`E2E_RESET_CONFIRM`（bool、既定false）がtrueで
ない場合は何もせず終了する。`compose.e2e.yml`はこの変数をbackendサービスにのみ渡すため、
dev/it/prod用のcomposeオーバーレイ経由でこのツールを実行してしまってもtrueにはならない
（IT・SIGNUP_ENABLED等と同じく`.env`から渡す一本の経路に統一し、コマンドラインでの
都度指定はしない）。

`backend/data/init_user.json`・`init_persona.json`はE2Eでも同じもの（各自ローカル用意）を使う。
E2E専用の追加データは不要。

### 5.5 実行コマンド

backend・frontendのポートは`compose.e2e.yml`側で`E2E_BACKEND_PORT`（既定8100）・
`E2E_FRONTEND_PORT`（既定3100）に固定しているため、devスタック（8000/3000）と同時に
起動してもホストポートは衝突しない。

```bash
# 1. スキーマ最新化（冪等）
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend alembic upgrade head

# 2. データリセット（TRUNCATE + 初期データ再投入。.envのE2E_RESET_CONFIRM=trueが必要）
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm backend python -m tools.reset_e2e_data

# 3. backend/frontendをDockerfile.prodでビルド・起動（-pで別プロジェクト名にしdevスタックと分離）
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e up -d --build backend frontend

# 4. Playwright実行（frontendとネットワーク名前空間を共有し http://127.0.0.1:3000 へアクセス）
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e run --rm --build e2e

# 5. 後片付け
docker compose -f compose.yml -f compose.e2e.yml -p gpc-e2e down
```

### 5.6 シナリオの一覧

happy pathに加え、認証・認可、ペルソナ閲覧、チャット作成・履歴・削除、メッセージ送受信の
分岐・異常系を以下のファイルに分けて網羅している。ファイルを分けているのは、LLM呼び出しを
伴うシナリオ（`chat-messaging.spec.ts`）とそうでないシナリオを区別し、後者だけを素早く
実行できるようにするため（`npx playwright test --grep-invert`等での部分実行を想定）。

| ファイル | 内容 | LLM呼び出し |
| --- | --- | --- |
| `happy-path.spec.ts` | サインアップ→ペルソナ選択→チャット送信までの一直線のhappy path | あり |
| `auth.spec.ts` | サインアップ・ログインのバリデーション、重複ID、誤パスワード、存在しないID、連続失敗によるロックアウト（`LOGIN_FAILURE_LIMIT`）、未ログイン時の各保護ページへのリダイレクト、ログアウト | なし |
| `personas.spec.ts` | ペルソナ一覧の検索・0件表示、詳細画面の表示・「一覧に戻る」・「チャットを始める」からの事前選択、存在しないpersona_idへのリダイレクト | なし |
| `chat-creation.spec.ts` | ペルソナ選択の上限（`CHAT_PERSONA_MAX_COUNT`）・下限、チャットモード切替とお題必須判定、チャット履歴一覧の表示・空状態・削除（キャンセル／OK） | なし |
| `chat-messaging.spec.ts` | メッセージ入力の上限文字数・空白のみ送信不可、送信直後の自分の発言表示とペルソナ応答、PERSONA_ONLYモードでの会話進行 | あり |

ペルソナ数に依存するシナリオ（選択上限超過・PERSONA_ONLYの複数ペルソナ会話）は、
`backend/data/init_persona.json`（各自ローカル用意、5.4節参照）の件数が足りない場合に
`test.skip`で自動的にスキップする。

### 5.7 既知の制約

- CIは未整備（4.4節と同様、今後の課題）。
- フルスイート（33件、`workers: 2`）を通しで流すと、実LLM APIへの同時呼び出しが重なる
  タイミング次第で、LLM応答待ちの個別テストがまれに`timeout`ぎりぎりで失敗することがある
  （単独実行では毎回安定して成功する）。コードの不具合ではなく実行環境の負荷起因のため、
  失敗したテストだけ再実行すれば通常は成功する。気になる場合は`workers: 1`に落として
  直列実行するとより安定する。

---

## 6. Playwright MCP（Claude Code用）

5節のE2Eとは別物。`compose.e2e.yml`の`e2e`サービスは自動テストを使い捨てコンテナで回す
仕組みだが、こちらはClaude Codeが対話的にブラウザを操作して画面を確認・調査するための
MCPサーバー設定（`.mcp.json`、repo root、コミット対象）。

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

- `--headless`: devContainerにディスプレイはないため必須。
- `--isolated`: 毎回使い捨てのブラウザプロファイルを使う（永続化しない）。

### 6.1 対象はfrontend devContainerのみ

backend devContainerはPython環境でNode/ブラウザを持たないため対象外とした。ブラウザ操作は
frontend devContainer側で行う前提。

### 6.2 devContainer側の準備

Chromium本体（`~/.cache/ms-playwright`、数百MB）をイメージ再ビルドのたびに毎回
再ダウンロードしないよう、OSライブラリのインストールとブラウザ本体の取得を分けている。

- **OS側の共有ライブラリ（`libnss3`等）**: `frontend/Dockerfile.dev`に
  `npx playwright install-deps chromium`を追加済み（`Dockerfile.e2e`の
  `install --with-deps`と似た手法だが、ブラウザ本体のダウンロードは含めない。
  5.1節参照）。イメージに焼き込まれるため、イメージ再ビルド時のみ実行される。
- **Chromium本体**: `compose.dev.yml`のfrontendサービスに`frontend_playwright_cache`
  named volumeを追加し、`/root/.cache/ms-playwright`（Playwrightのデフォルトの
  ダウンロード先）にマウントしている。本体のダウンロードは
  `.devcontainer/frontend/devcontainer.json`の`postCreateCommand`
  （`npx playwright install chromium`）で行う。volumeに既にキャッシュ済みなら
  再ダウンロードはスキップされるため、イメージを再ビルドしてもコンテナを再作成
  （postCreateCommand再実行）するだけで済み、ダウンロードは初回のみで済む。

- 既存のfrontend devContainerを使っている場合は、`compose.dev.yml`・
  `Dockerfile.dev`の変更を反映するためイメージの再ビルドが必要
  （VS Code等の「Rebuild Container」。postCreateCommandも合わせて再実行される）。
- MCPサーバー自体（`@playwright/mcp`）はバージョン固定せず`npx`でその都度取得する
  ため、事前インストールの対象にはしていない。

### 6.3 到達先

frontend devContainerの`frontend`サービス自体が`npm run dev`（port 3000）を実行して
いるため、同じコンテナ内で動くMCPサーバーからは`http://localhost:3000`でNext.js dev
サーバーへ到達できる（5.1節のE2Eのようなコンテナ間のCookie・DNSの制約はない）。

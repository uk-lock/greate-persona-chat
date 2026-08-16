# テーブル設計

## m_user

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | ユーザID |
| login_id | VARCHAR(255) | ○ | UK | ログインID |
| password_hash | VARCHAR(255) | ○ |  | パスワードハッシュ |
| failed_login_count | INT | ○ |  | ログイン連続失敗回数 |
| locked_until | DATETIME |  |  | ロック解除日時（未ロック時はNULL） |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

### 備考

- `failed_login_count` が10に達した時点で `locked_until` に現在時刻+15分を設定してログインをロックする。ログイン成功時、または `locked_until` 経過後は `failed_login_count` を0、`locked_until` をNULLにリセットする。
- `login_id` は半角英数字のみを許容する（記号・日本語等のマルチバイト文字は不可）。管理者発行・セルフサインアップのいずれで作成されたアカウントにも共通して適用する制約とする。

---

## m_persona

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | ペルソナID |
| name | VARCHAR(255) | ○ |  | ペルソナ名 |
| image_url | VARCHAR(255) |  |  | 肖像画像URL |
| country | VARCHAR(255) |  |  | 国 |
| era | VARCHAR(255) |  |  | 年代 |
| summary | TEXT |  |  | 概要 |
| description | TEXT |  |  | 詳細説明 |
| personality | TEXT |  |  | 性格 |
| conversation_policy | TEXT |  |  | 会話方針（会話でのポジション・語尾等） |
| biography | JSONB |  |  | 経歴（年表） |
| sample_quotes | JSONB |  |  | 発言例（文字列配列） |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

### 備考

- `conversation_policy` はその人物がどんな会話のポジション・語尾等で話すかを表す自由テキストで、
  LLMの応答生成プロンプトにのみ使う内部項目。ペルソナ一覧・詳細のAPIレスポンスには含めず、
  フロント側の画面にも表示しない（[api.md](./api.md) Personas節参照）。
- `biography` は `[{"year": 1780, "event": "XXXをした"}, ...]` のような、年（`year`：数値）と出来事（`event`：文字列）を持つオブジェクト配列のJSONを想定する。
- `sample_quotes` は `["発言例1", "発言例2", ...]` のような文字列配列のJSONを想定する。
- `image_url` が `NULL` の場合、画面側でデフォルトのプレースホルダー画像を表示する。

---

## t_chat

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | チャットID（内部PK） |
| public_id | UUID | ○ | UK | 外部公開用チャットID（URL・APIレスポンスで使用） |
| user_id | BIGINT | ○ | FK | ユーザID |
| title | VARCHAR(255) | ○ |  | チャットタイトル |
| chat_mode | VARCHAR(50) | ○ |  | チャットモード |
| topic | VARCHAR(255) |  |  | 会話のお題（PERSONA_ONLYのみ） |
| is_stopped | BOOLEAN | ○ |  | 会話停止フラグ |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |


### 備考

- `chat_mode` は以下の値を想定する。
  - `PERSONA_ONLY`: ペルソナ同士のみの会話
  - `USER_PARTICIPATED`: ユーザが参加する会話
- `title` はチャット作成時点では固定文言（例：「新規チャット」）で登録し、会話が進んだ後にLLMが内容から生成したタイトルで更新する。
- `topic` はPERSONA_ONLYモードでのみユーザーがチャット作成時に入力する、ペルソナ同士の自動会話の方向づけ用テキスト。USER_PARTICIPATEDではNULL（ユーザー自身が会話を主導するため不要）。ペルソナ応答生成・話者選択のLLMプロンプトへ毎ターン差し込むことで、会話履歴が流れても方向性を保つ（[api.md](./api.md) POST /chats参照）。
- `public_id`は連番の`id`をURL・APIレスポンスにそのまま露出させない（推測・列挙されない）ための識別子。`t_chat_message`・`t_chat_persona`のFKは引き続き内部PK（`id`）を参照し、`public_id`は`t_chat`単体の識別子として追加する。アプリ側で`uuid.uuid4()`により生成する（DB側のデフォルト生成は使わない）。

---

## t_chat_persona

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | チャットペルソナID |
| chat_id | BIGINT | ○ | FK | チャットID |
| persona_id | BIGINT | ○ | FK | ペルソナID |
| sort_no | INT | ○ | UK | 表示順・発言順 |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

### 備考

- `sort_no` は `chat_id` ごとに一意とする（複合ユニーク: `chat_id` + `sort_no`）。

---

## t_chat_message

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | メッセージID |
| chat_id | BIGINT | ○ | FK | チャットID |
| persona_id | BIGINT |  | FK | ペルソナID |
| sort_no | INT | ○ | UK | メッセージ順 |
| speaker_type | VARCHAR(50) | ○ |  | 発話者種別 |
| message | TEXT | ○ |  | メッセージ本文 |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

### 備考

- `speaker_type` は以下の値を想定する。
  - `USER`: ユーザ発言
  - `PERSONA`: ペルソナ発言
- `speaker_type = PERSONA` の場合、`persona_id` は必須。
- `speaker_type = USER` の場合、`persona_id` は `NULL` とする。
- `sort_no` は `chat_id` ごとに一意とする（複合ユニーク: `chat_id` + `sort_no`）。
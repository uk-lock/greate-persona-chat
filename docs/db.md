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
| biography | TEXT |  |  | 経歴 |
| sample_quotes | JSONB |  |  | 発言例（文字列配列） |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

### 備考

- `sample_quotes` は `["発言例1", "発言例2", ...]` のような文字列配列のJSONを想定する。
- `image_url` が `NULL` の場合、画面側でデフォルトのプレースホルダー画像を表示する。

---

## t_chat

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | チャットID |
| user_id | BIGINT | ○ | FK | ユーザID |
| title | VARCHAR(255) | ○ |  | チャットタイトル |
| chat_mode | VARCHAR(50) | ○ |  | チャットモード |
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
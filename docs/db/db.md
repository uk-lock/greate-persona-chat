# テーブル設計

## m_user

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | ユーザID |
| login_id | VARCHAR(255) | ○ | UK | ログインID |
| password_hash | VARCHAR(255) | ○ |  | パスワードハッシュ |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

---

## m_persona

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | ペルソナID |
| name | VARCHAR(255) | ○ |  | ペルソナ名 |
| country | VARCHAR(255) |  |  | 国 |
| summary | TEXT |  |  | 概要 |
| description | TEXT |  |  | 詳細説明 |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

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

---

## t_chat_persona

| カラム名 | データ型 | NOT NULL | Key | 概要 |
|---|---:|:---:|---|---|
| id | BIGINT | ○ | PK | チャットペルソナID |
| chat_id | BIGINT | ○ | FK | チャットID |
| persona_id | BIGINT | ○ | FK | ペルソナID |
| sort_no | INT | ○ |  | 表示順・発言順 |
| is_deleted | BOOLEAN | ○ |  | 論理削除フラグ |
| created_at | DATETIME | ○ |  | 作成日時 |
| updated_at | DATETIME | ○ |  | 更新日時 |
| created_by | VARCHAR(255) | ○ |  | 作成者 |
| updated_by | VARCHAR(255) | ○ |  | 更新者 |

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
- `speaker_type = USER` または `SYSTEM` の場合、`persona_id` は `NULL` とする。
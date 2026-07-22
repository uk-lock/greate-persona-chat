# API設計

## Auth

### ログイン

```http
POST /auth/login
```

ログインID・パスワードを検証し、JWTをHttpOnly Cookieに設定する。

---

### ログアウト

```http
POST /auth/logout
```

Cookieに設定されたJWTを破棄する。

---

## Chats

### チャット一覧取得

```http
GET /chats
```

チャット履歴画面で、ログインユーザのチャット一覧を取得する。

---

### チャット作成

```http
POST /chats
```

新規チャット画面で、選択したペルソナをもとにチャットを作成する。

---

### チャット削除

```http
DELETE /chats/{chat_id}
```

チャット履歴画面で、指定したチャットを削除する。

---

### メッセージ一覧取得

```http
GET /chats/{chat_id}/messages
```

チャット画面で、指定したチャットのメッセージ一覧を取得する。

---

### メッセージ送信（会話進行トリガー）

```http
POST /chats/{chat_id}/messages
```

チャット画面で、会話を1ターン進める。`chat_mode` により振る舞いが異なる。

- `USER_PARTICIPATED`：リクエストボディのユーザー発言を保存した上で、文脈に応じてLLMが選択したペルソナの応答をSSE（Server-Sent Events）でストリーミング配信する。応答後、LLMが「会話を続けるべき」と判断した場合は、別のペルソナが連鎖して発言することがある（安全弁として連鎖回数の上限を設ける）。「連鎖が自然に終わる」か「上限に達する」か「ユーザが会話を停止させる」と、制御はユーザーに戻る。
- `PERSONA_ONLY`：リクエストボディなし。ペルソナ同士の会話をサーバー側で連続生成し、生成された発言を都度SSEでストリーミング配信し続ける（`stop` が呼ばれるまで継続）。

---

### 会話停止

```http
POST /chats/{chat_id}/stop
```

自動進行中・連鎖発言中の会話を中断する。`PERSONA_ONLY` の自動進行、`USER_PARTICIPATED` のペルソナ連鎖発言のいずれも、このAPIで即座に中断してユーザーに制御を戻せる。`t_chat.is_stopped` を `true` に更新する。

---

## Personas

### ペルソナ一覧取得

```http
GET /personas
```

新規チャット画面およびペルソナ一覧画面で、ペルソナ一覧を取得する。

---

### ペルソナ詳細取得

```http
GET /personas/{persona_id}
```

ペルソナ詳細画面で、指定したペルソナの詳細情報を取得する。

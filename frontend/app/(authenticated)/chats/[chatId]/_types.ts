export type ChatMode = "USER_PARTICIPATED" | "PERSONA_ONLY";

/** チャット参加者（`GET /chats/{chat_id}`のレスポンス。api.md参照）。 */
export type Participant =
  | { type: "USER"; name: string }
  | { type: "PERSONA"; persona_id: number; name: string; image_url: string | null };

/** `GET /chats/{chat_id}`のレスポンス（api.md参照）。
 *
 * `chat_id`は`t_chat.public_id`（UUID文字列）。連番の内部PKは公開しない。
 */
export type ChatDetail = {
  chat_id: string;
  title: string;
  chat_mode: ChatMode;
  topic: string | null;
  updated_at: string;
  participants: Participant[];
};

/** `GET /chats/{chat_id}/messages`の1件（api.md参照）。 */
export type ChatMessage = {
  id: number;
  sort_no: number;
  speaker_type: "USER" | "PERSONA";
  persona_id: number | null;
  message: string;
  created_at: string;
};

/** `POST /chats/{chat_id}/messages`のSSEイベント（判別ユニオン。api.md参照）。 */
export type ChatStreamEvent =
  | { type: "thinking"; persona_id: number }
  | { type: "message"; message: ChatMessage }
  | { type: "title"; title: string }
  | { type: "error"; message: string };

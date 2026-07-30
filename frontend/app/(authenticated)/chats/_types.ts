/** チャット参加者（S02-chat-history.md 10節）。 */
export type Participant =
  | { type: "USER"; name: string }
  | { type: "PERSONA"; persona_id: number; name: string; image_url: string | null };

export type ChatMode = "USER_PARTICIPATED" | "PERSONA_ONLY";

/** `GET /chats`のレスポンス1件分（api.md参照）。 */
export type Chat = {
  chat_id: number;
  title: string;
  chat_mode: ChatMode;
  updated_at: string;
  participants: Participant[];
};

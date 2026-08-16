import type { ChatStreamEvent } from "./_types";

/** バッファを`\n\n`区切りのSSEイベント群と、まだ完結していない残り部分に分割する。 */
export const splitSseFrames = (buffer: string): { frames: string[]; remainder: string } => {
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  return { frames: parts, remainder };
};

/** SSEの1イベント（`data: {...}`形式）からChatStreamEventを取り出す。dataフレームでなければnull。 */
export const parseSseFrame = (frame: string): ChatStreamEvent | null => {
  const dataLine = frame.split("\n").find((line) => line.startsWith("data: "));
  if (!dataLine) {
    return null;
  }
  return JSON.parse(dataLine.slice("data: ".length)) as ChatStreamEvent;
};

/** SSEレスポンスのReaderを読み進め、受信したイベントを逐次`onEvent`へ渡す。
 *
 * バックエンドの`message`イベントは常に1件の完成した発言であり、トークン単位の
 * ストリーミングは行わない。応答生成中であることは`thinking`イベントで示す
 * （呼び出し側〈chat-room.tsx〉がイベント種別ごとに表示を出し分ける）。
 */
export const consumeSseStream = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> => {
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const { frames, remainder } = splitSseFrames(buffer);
    buffer = remainder;
    for (const frame of frames) {
      const event = parseSseFrame(frame);
      if (event) {
        onEvent(event);
      }
    }
  }
};

/** SSEレスポンスが正常応答でなかった場合に送出するエラー。エラーバナー表示に使う。 */
export class MessageStreamError extends Error {}

type MessageStreamBody = {
  message?: string;
};

/** メッセージ送信・自動進行開始のSSEストリームを開始する。
 *
 * バックエンドはDocker Compose内部ホストでブラウザから直接到達できないため、
 * Next.jsのRoute Handler（app/api/chats/[chatId]/messages/route.ts）を経由して中継する。
 */
export const startMessageStream = async (
  chatId: string,
  body: MessageStreamBody,
  signal: AbortSignal,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> => {
  const response = await fetch(`/api/chats/${chatId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as { message?: string } | null;
    throw new MessageStreamError(errorBody?.message ?? "エラーが発生しました");
  }

  if (!response.body) {
    return;
  }
  await consumeSseStream(response.body.getReader(), onEvent);
};

import { describe, expect, test, vi } from "vitest";
import {
  consumeSseStream,
  parseSseFrame,
  splitSseFrames,
} from "@/app/(authenticated)/chats/[chatId]/_sse";

describe("splitSseFrames", () => {
  test("完結したイベントと未完結の残りに分割する", () => {
    const result = splitSseFrames('data: {"id":1}\n\ndata: {"id":2}\n\ndata: {"id":3');
    expect(result.frames).toEqual(['data: {"id":1}', 'data: {"id":2}']);
    expect(result.remainder).toBe('data: {"id":3');
  });

  test("完結したイベントが無い場合はremainderのみを返す", () => {
    const result = splitSseFrames('data: {"id":1}');
    expect(result.frames).toEqual([]);
    expect(result.remainder).toBe('data: {"id":1}');
  });
});

describe("parseSseFrame", () => {
  test("dataフレームからmessageイベントを取り出す", () => {
    const frame =
      'data: {"type":"message","message":{"id":1,"sort_no":1,"speaker_type":"USER","persona_id":null,"message":"こんにちは","created_at":"2026-07-30T09:00:00+09:00"}}';
    expect(parseSseFrame(frame)).toEqual({
      type: "message",
      message: {
        id: 1,
        sort_no: 1,
        speaker_type: "USER",
        persona_id: null,
        message: "こんにちは",
        created_at: "2026-07-30T09:00:00+09:00",
      },
    });
  });

  test("dataフレームからthinkingイベントを取り出す", () => {
    const frame = 'data: {"type":"thinking","persona_id":5}';
    expect(parseSseFrame(frame)).toEqual({ type: "thinking", persona_id: 5 });
  });

  test("dataフレームでない場合はnullを返す", () => {
    expect(parseSseFrame(": keep-alive")).toBeNull();
  });
});

describe("consumeSseStream", () => {
  test("複数チャンクにまたがるイベントも正しく読み進めてonEventへ渡す", async () => {
    const encoder = new TextEncoder();
    const chunks = [
      encoder.encode('data: {"type":"thinking",'),
      encoder.encode('"persona_id":5}\n\n'),
      encoder.encode(
        'data: {"type":"message","message":{"id":2,"sort_no":2,"speaker_type":"PERSONA","persona_id":5,"message":"b","created_at":"t"}}\n\n',
      ),
    ];
    let index = 0;
    const reader = {
      read: vi.fn(async () => {
        if (index < chunks.length) {
          const value = chunks[index];
          index += 1;
          return { done: false, value };
        }
        return { done: true, value: undefined };
      }),
    } as unknown as ReadableStreamDefaultReader<Uint8Array>;

    const onEvent = vi.fn();
    await consumeSseStream(reader, onEvent);

    expect(onEvent).toHaveBeenCalledTimes(2);
    expect(onEvent).toHaveBeenNthCalledWith(1, { type: "thinking", persona_id: 5 });
    expect(onEvent).toHaveBeenNthCalledWith(2, {
      type: "message",
      message: {
        id: 2,
        sort_no: 2,
        speaker_type: "PERSONA",
        persona_id: 5,
        message: "b",
        created_at: "t",
      },
    });
  });
});

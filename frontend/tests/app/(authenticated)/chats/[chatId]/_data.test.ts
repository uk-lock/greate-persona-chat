import { beforeEach, describe, expect, test, vi } from "vitest";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { fetchChatDetail, fetchMessages } from "@/app/(authenticated)/chats/[chatId]/_data";

const CHAT_ID = "11111111-1111-1111-1111-111111111111";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

vi.mock("@/lib/api-client", () => {
  class MockApiError extends Error {
    constructor(
      public readonly status: number,
      message: string,
    ) {
      super(message);
      this.name = "ApiError";
    }
  }
  return {
    ApiError: MockApiError,
    apiClient: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
  };
});

const mockedGet = vi.mocked(apiClient.get);
const mockedRedirect = vi.mocked(redirect);

describe("fetchChatDetail", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("取得に成功した場合はチャット詳細を返す", async () => {
    const chat = {
      chat_id: CHAT_ID,
      title: "新規チャット",
      chat_mode: "USER_PARTICIPATED",
      updated_at: "2026-07-30T09:00:00+09:00",
      participants: [{ type: "USER", name: "あなた" }],
    };
    mockedGet.mockResolvedValueOnce({ data: chat, setCookie: [] });

    await expect(fetchChatDetail(CHAT_ID, "access_token=abc")).resolves.toEqual(chat);
    expect(mockedRedirect).not.toHaveBeenCalled();
  });

  test("401の場合はS00（/login）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(401, "認証が必要です"));

    await expect(fetchChatDetail(CHAT_ID, undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/login");
  });

  test("404の場合はS02（/chats）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(404, "見つかりません"));

    await expect(fetchChatDetail(CHAT_ID, undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/chats");
  });

  test("403の場合も404と同様にS02（/chats）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(403, "権限がありません"));

    await expect(fetchChatDetail(CHAT_ID, undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/chats");
  });

  test("404・403以外のエラーはリダイレクトせず送出する", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(500, "エラーが発生しました"));

    await expect(fetchChatDetail(CHAT_ID, undefined)).rejects.toThrow("エラーが発生しました");
    expect(mockedRedirect).not.toHaveBeenCalled();
  });
});

describe("fetchMessages", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("メッセージ一覧を返す", async () => {
    const messages = [
      {
        id: 1,
        sort_no: 1,
        speaker_type: "USER",
        persona_id: null,
        message: "こんにちは",
        created_at: "2026-07-30T09:00:00+09:00",
      },
    ];
    mockedGet.mockResolvedValueOnce({ data: messages, setCookie: [] });

    await expect(fetchMessages(CHAT_ID, undefined)).resolves.toEqual(messages);
  });
});

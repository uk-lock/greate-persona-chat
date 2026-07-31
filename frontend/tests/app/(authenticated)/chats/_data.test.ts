import { beforeEach, describe, expect, test, vi } from "vitest";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { fetchChats } from "@/app/(authenticated)/chats/_data";

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

describe("fetchChats", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("取得に成功した場合はチャット一覧を返す", async () => {
    const chats = [
      {
        chat_id: "11111111-1111-1111-1111-111111111111",
        title: "新規チャット",
        chat_mode: "USER_PARTICIPATED",
        updated_at: "2026-07-30T09:00:00+09:00",
        participants: [{ type: "USER", name: "あなた" }],
      },
    ];
    mockedGet.mockResolvedValueOnce({ data: chats, setCookie: [] });

    await expect(fetchChats("access_token=abc")).resolves.toEqual(chats);
    expect(mockedRedirect).not.toHaveBeenCalled();
  });

  test("401の場合はS00（/login）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(401, "認証が必要です"));

    await expect(fetchChats(undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/login");
  });

  test("401以外のエラーはリダイレクトせず送出する", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(500, "エラーが発生しました"));

    await expect(fetchChats(undefined)).rejects.toThrow("エラーが発生しました");
    expect(mockedRedirect).not.toHaveBeenCalled();
  });
});

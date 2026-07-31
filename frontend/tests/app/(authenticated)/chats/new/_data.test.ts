import { beforeEach, describe, expect, test, vi } from "vitest";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { fetchPersonaOptions } from "@/app/(authenticated)/chats/new/_data";

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

describe("fetchPersonaOptions", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("取得に成功した場合はペルソナ一覧を返す", async () => {
    const personas = [{ id: 1, name: "織田信長", image_url: null, summary: null }];
    mockedGet.mockResolvedValueOnce({ data: personas, setCookie: [] });

    await expect(fetchPersonaOptions("access_token=abc")).resolves.toEqual(personas);
    expect(mockedRedirect).not.toHaveBeenCalled();
  });

  test("401の場合はS00（/login）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(401, "認証が必要です"));

    await expect(fetchPersonaOptions(undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/login");
  });

  test("401以外のエラーはリダイレクトせず送出する", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(500, "エラーが発生しました"));

    await expect(fetchPersonaOptions(undefined)).rejects.toThrow("エラーが発生しました");
    expect(mockedRedirect).not.toHaveBeenCalled();
  });
});

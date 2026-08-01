import { beforeEach, describe, expect, test, vi } from "vitest";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { fetchPersona } from "@/app/(authenticated)/personas/[personaId]/_data";

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

describe("fetchPersona", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("取得に成功した場合はペルソナ詳細を返す", async () => {
    const persona = {
      id: 1,
      name: "織田信長",
      image_url: null,
      country: "日本",
      era: "戦国時代",
      summary: "概要",
      description: "詳細",
      personality: "性格",
      biography: [{ year: 1560, event: "経歴" }],
      sample_quotes: ["是非に及ばず"],
    };
    mockedGet.mockResolvedValueOnce({ data: persona, setCookie: [] });

    await expect(fetchPersona(1, "access_token=abc")).resolves.toEqual(persona);
    expect(mockedRedirect).not.toHaveBeenCalled();
  });

  test("401の場合はS00（/login）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(401, "認証が必要です"));

    await expect(fetchPersona(1, undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/login");
  });

  test("404の場合はS04（/personas）へリダイレクトする", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(404, "見つかりません"));

    await expect(fetchPersona(999, undefined)).rejects.toThrow();
    expect(mockedRedirect).toHaveBeenCalledWith("/personas");
  });

  test("401・404以外のエラーはリダイレクトせず送出する", async () => {
    mockedGet.mockRejectedValueOnce(new ApiError(500, "エラーが発生しました"));

    await expect(fetchPersona(1, undefined)).rejects.toThrow("エラーが発生しました");
    expect(mockedRedirect).not.toHaveBeenCalled();
  });
});

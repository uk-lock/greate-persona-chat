import { describe, expect, test } from "vitest";
import { getAuthCookieHeader, parseSetCookie } from "@/lib/cookie";
import { AUTH_COOKIE_NAME } from "@/lib/constants";

describe("parseSetCookie", () => {
  test("バックエンドが発行するCookie属性を解析できる", () => {
    const header =
      "access_token=abc.def.ghi; HttpOnly; Path=/; SameSite=Lax; Secure; Max-Age=86400";

    expect(parseSetCookie(header)).toEqual({
      name: "access_token",
      value: "abc.def.ghi",
      options: {
        httpOnly: true,
        path: "/",
        sameSite: "lax",
        secure: true,
        maxAge: 86400,
      },
    });
  });

  test("name=valueの形式でない場合はnullを返す", () => {
    expect(parseSetCookie("invalid-cookie-header")).toBeNull();
  });
});

describe("getAuthCookieHeader", () => {
  const buildCookieStore = (value?: string) =>
    ({
      get: (name: string) =>
        name === AUTH_COOKIE_NAME && value !== undefined ? { name, value } : undefined,
    }) as unknown as Parameters<typeof getAuthCookieHeader>[0];

  test("認証Cookieが存在する場合はヘッダー文字列を返す", () => {
    expect(getAuthCookieHeader(buildCookieStore("abc.def.ghi"))).toBe(
      `${AUTH_COOKIE_NAME}=abc.def.ghi`,
    );
  });

  test("認証Cookieが存在しない場合はundefinedを返す", () => {
    expect(getAuthCookieHeader(buildCookieStore())).toBeUndefined();
  });
});

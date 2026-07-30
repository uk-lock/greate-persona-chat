import { describe, expect, test } from "vitest";
import { parseSetCookie } from "@/lib/cookie";

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

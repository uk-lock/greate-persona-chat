import { describe, expect, test } from "vitest";
import { loginSchema } from "@/lib/schemas/auth";

describe("loginSchema", () => {
  test("login_id・passwordが入力されていれば成功する", () => {
    const result = loginSchema.safeParse({ login_id: "taro", password: "secret" });
    expect(result.success).toBe(true);
  });

  test("login_idが空の場合はエラーになる", () => {
    const result = loginSchema.safeParse({ login_id: "", password: "secret" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.flatten().fieldErrors.login_id).toContain(
        "ログインIDを入力してください",
      );
    }
  });

  test("passwordが空の場合はエラーになる", () => {
    const result = loginSchema.safeParse({ login_id: "taro", password: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.flatten().fieldErrors.password).toContain(
        "パスワードを入力してください",
      );
    }
  });

  test("256文字以上のlogin_idはエラーになる", () => {
    const result = loginSchema.safeParse({
      login_id: "a".repeat(256),
      password: "secret",
    });
    expect(result.success).toBe(false);
  });

  test("login_idに半角英数字以外が含まれる場合はエラーになる", () => {
    const result = loginSchema.safeParse({ login_id: "taro太郎", password: "secret" });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.flatten().fieldErrors.login_id).toContain(
        "ログインIDは半角英数字で入力してください",
      );
    }
  });
});

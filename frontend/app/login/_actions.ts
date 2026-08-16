"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { applySetCookies } from "@/lib/cookie";
import { loginSchema, type LoginFormValues } from "@/lib/schemas/auth";

export type LoginActionResult = { formError: string } | undefined;

/** ログインID・パスワードを検証し、成功時はCookie設定後にS02（/chats）へ遷移する。
 *
 * バックエンドへのfetchはNext.jsサーバー側から行われるため、バックエンドが返す
 * `Set-Cookie`はブラウザに直接届かない。ここで明示的にNext.js側のCookieへ設定し直す。
 */
export const loginAction = async (values: LoginFormValues): Promise<LoginActionResult> => {
  const parsed = loginSchema.safeParse(values);
  if (!parsed.success) {
    return { formError: "入力内容を確認してください" };
  }

  let setCookie: string[];
  try {
    const result = await apiClient.post<Record<string, never>>("/auth/login", parsed.data);
    setCookie = result.setCookie;
  } catch (error) {
    if (error instanceof ApiError) {
      return { formError: error.message };
    }
    return { formError: "ログインに失敗しました。時間をおいて再度お試しください。" };
  }

  const cookieStore = await cookies();
  applySetCookies(cookieStore, setCookie);
  redirect("/chats");
};

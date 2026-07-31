"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { applySetCookies } from "@/lib/cookie";
import { signupSchema, type SignupFormValues } from "@/lib/schemas/auth";

export type SignupActionResult = { formError: string } | undefined;

/** ログインID・パスワードを登録し、成功時はCookie設定後にS02（/chats）へ遷移する（自動ログイン）。
 *
 * `password_confirm`はフロントエンド内の一致確認にのみ使い、APIリクエストには含めない
 * （S06-signup.md 10節）。
 */
export const signupAction = async (values: SignupFormValues): Promise<SignupActionResult> => {
  const parsed = signupSchema.safeParse(values);
  if (!parsed.success) {
    return { formError: "入力内容を確認してください" };
  }

  let setCookie: string[];
  try {
    const result = await apiClient.post<Record<string, never>>("/auth/signup", {
      login_id: parsed.data.login_id,
      password: parsed.data.password,
    });
    setCookie = result.setCookie;
  } catch (error) {
    if (error instanceof ApiError) {
      return { formError: error.message };
    }
    return { formError: "登録に失敗しました。時間をおいて再度お試しください。" };
  }

  const cookieStore = await cookies();
  applySetCookies(cookieStore, setCookie);
  redirect("/chats");
};

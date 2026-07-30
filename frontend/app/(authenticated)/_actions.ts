"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { applySetCookies, getAuthCookieHeader } from "@/lib/cookie";
import { AUTH_COOKIE_NAME } from "@/lib/constants";

/** サイドバーのログアウト操作。バックエンドにCookie破棄を依頼し、S00（/login）へ遷移する。
 *
 * バックエンドへの通信が失敗した場合も、ユーザー自身のセッションを終了させることを優先し、
 * Next.js側のCookieを直接削除した上でログイン画面へ遷移する。
 */
export const logoutAction = async (): Promise<void> => {
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);

  try {
    const result = await apiClient.post<Record<string, never>>(
      "/auth/logout",
      undefined,
      cookieHeader,
    );
    applySetCookies(cookieStore, result.setCookie);
  } catch {
    cookieStore.delete(AUTH_COOKIE_NAME);
  }

  redirect("/login");
};

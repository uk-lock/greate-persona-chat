"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { getAuthCookieHeader } from "@/lib/cookie";

export type StopChatActionResult = { error: string } | undefined;

/** 自動進行中・連鎖発言中の会話を中断する（`POST /chats/{chat_id}/stop`）。
 *
 * クライアント側でもストリームのfetchをAbortControllerで中断するが（即座にUIへ反映するため）、
 * サーバー側のPERSONA_ONLY自動進行ループを確実に止めるため、こちらも合わせて呼び出す。
 */
export const stopChatAction = async (chatId: string): Promise<StopChatActionResult> => {
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);

  try {
    await apiClient.post(`/chats/${chatId}/stop`, undefined, cookieHeader);
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        redirect("/login");
      }
      return { error: error.message };
    }
    return { error: "停止に失敗しました。時間をおいて再度お試しください。" };
  }

  return undefined;
};

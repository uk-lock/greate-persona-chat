"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { getAuthCookieHeader } from "@/lib/cookie";

export type DeleteChatActionResult = { error: string } | undefined;

/** チャット削除（`DELETE /chats/{chat_id}`）。削除確認ダイアログでOKが押された際に呼び出す。 */
export const deleteChatAction = async (chatId: string): Promise<DeleteChatActionResult> => {
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);

  try {
    await apiClient.delete(`/chats/${chatId}`, cookieHeader);
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        redirect("/login");
      }
      return { error: error.message };
    }
    return { error: "削除に失敗しました。時間をおいて再度お試しください。" };
  }

  // 一覧はChatList側で楽観的にクライアント状態を更新しているが、ルーターキャッシュに
  // 残った古い一覧を後から再訪した際に見せないよう、サーバー側のキャッシュも無効化する。
  revalidatePath("/chats");
  return undefined;
};

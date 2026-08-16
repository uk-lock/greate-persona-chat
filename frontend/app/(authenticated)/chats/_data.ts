import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import type { Chat } from "./_types";

/** チャット一覧を取得する（`GET /chats`）。
 *
 * Cookieは存在するがJWTが無効・期限切れの場合、バックエンドは401を返す。
 * このケースを検知し、S00（/login）へリダイレクトする（frontend_login-followup.md参照）。
 */
export const fetchChats = async (cookieHeader: string | undefined): Promise<Chat[]> => {
  try {
    const result = await apiClient.get<Chat[]>("/chats", cookieHeader);
    return result.data;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
};

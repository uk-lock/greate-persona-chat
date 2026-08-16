import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import type { ChatDetail, ChatMessage } from "./_types";

/** チャット単体を取得する（`GET /chats/{chat_id}`、ヘッダー表示用）。
 *
 * Cookieが無効・期限切れ（401）ならS00（/login）へ、チャットが存在しない・削除済み・
 * 他ユーザーのチャット（404／403）ならS02（/chats）へリダイレクトする。他ユーザーの
 * チャットであることを画面上で判別させないため、404と403は区別しない
 * （S03-chat.md 8節）。
 */
export const fetchChatDetail = async (
  chatId: string,
  cookieHeader: string | undefined,
): Promise<ChatDetail> => {
  try {
    const result = await apiClient.get<ChatDetail>(`/chats/${chatId}`, cookieHeader);
    return result.data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        redirect("/login");
      }
      if (error.status === 404 || error.status === 403) {
        redirect("/chats");
      }
    }
    throw error;
  }
};

/** メッセージ履歴を取得する（`GET /chats/{chat_id}/messages`）。
 *
 * 直前の`fetchChatDetail`で同一チャットの所有者チェックが済んでいる前提のため、
 * ここでは404／403の個別ハンドリングは行わない。
 */
export const fetchMessages = async (
  chatId: string,
  cookieHeader: string | undefined,
): Promise<ChatMessage[]> => {
  const result = await apiClient.get<ChatMessage[]>(`/chats/${chatId}/messages`, cookieHeader);
  return result.data;
};

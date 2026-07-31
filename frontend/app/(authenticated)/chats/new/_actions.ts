"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import { getAuthCookieHeader } from "@/lib/cookie";
import type { ChatMode } from "./_types";

export type CreateChatActionResult = { error: string } | undefined;

type CreateChatResponse = {
  chat_id: string;
};

/** 新規チャットを作成する（`POST /chats`）。成功時はS03（/chats/{chat_id}）へ遷移する。 */
export const createChatAction = async (
  personaIds: number[],
  chatMode: ChatMode,
): Promise<CreateChatActionResult> => {
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);

  let chat: CreateChatResponse;
  try {
    const result = await apiClient.post<CreateChatResponse>(
      "/chats",
      { persona_ids: personaIds, chat_mode: chatMode },
      cookieHeader,
    );
    chat = result.data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        redirect("/login");
      }
      return { error: error.message };
    }
    return { error: "チャットの作成に失敗しました。時間をおいて再度お試しください。" };
  }

  redirect(`/chats/${chat.chat_id}`);
};

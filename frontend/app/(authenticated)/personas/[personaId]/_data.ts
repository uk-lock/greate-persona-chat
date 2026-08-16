import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import type { PersonaDetail } from "./_types";

/** ペルソナ詳細を取得する（`GET /personas/{persona_id}`）。
 *
 * Cookieが無効・期限切れ（401）ならS00（/login）へリダイレクトする。対象が存在しない・
 * 削除済み（404）の場合はエラー画面を出さず、S04（/personas）へリダイレクトする
 * （S05-persona-detail.md 8節）。それ以外のエラーはそのまま送出し、error.tsxに委ねる。
 */
export const fetchPersona = async (
  personaId: number,
  cookieHeader: string | undefined,
): Promise<PersonaDetail> => {
  try {
    const result = await apiClient.get<PersonaDetail>(`/personas/${personaId}`, cookieHeader);
    return result.data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        redirect("/login");
      }
      if (error.status === 404) {
        redirect("/personas");
      }
    }
    throw error;
  }
};

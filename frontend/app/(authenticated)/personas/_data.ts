import { redirect } from "next/navigation";
import { ApiError, apiClient } from "@/lib/api-client";
import type { PersonaSummary } from "./_types";

/** ペルソナ一覧を取得する（`GET /personas`）。
 *
 * Cookieは存在するがJWTが無効・期限切れの場合、バックエンドは401を返す。
 * このケースを検知し、S00（/login）へリダイレクトする（frontend_login-followup.md参照）。
 */
export const fetchPersonas = async (
  cookieHeader: string | undefined,
): Promise<PersonaSummary[]> => {
  try {
    const result = await apiClient.get<PersonaSummary[]>("/personas", cookieHeader);
    return result.data;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
};

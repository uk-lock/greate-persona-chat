/** S01で選択候補として表示するペルソナ（`GET /personas`のレスポンス1件分。api.md参照）。 */
export type PersonaOption = {
  id: number;
  name: string;
  image_url: string | null;
  summary: string | null;
};

export type ChatMode = "USER_PARTICIPATED" | "PERSONA_ONLY";

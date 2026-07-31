/** `GET /personas/{persona_id}`のレスポンス（api.md参照）。 */
export type PersonaDetail = {
  id: number;
  name: string;
  image_url: string | null;
  country: string | null;
  era: string | null;
  summary: string | null;
  description: string | null;
  personality: string | null;
  biography: string | null;
  sample_quotes: string[] | null;
};

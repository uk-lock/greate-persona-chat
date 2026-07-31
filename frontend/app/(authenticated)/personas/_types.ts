/** `GET /personas`のレスポンス1件分（api.md参照）。 */
export type PersonaSummary = {
  id: number;
  name: string;
  image_url: string | null;
  summary: string | null;
};

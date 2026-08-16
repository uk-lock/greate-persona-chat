import "server-only";
import { config } from "./config";

/** GCEメタデータサーバーの Identity token エンドポイント（Cloud Run上でのみ到達可能）。
 * https://cloud.google.com/docs/authentication/get-id-token#metadata-server
 */
const METADATA_IDENTITY_URL =
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity";

/** Googleが発行するIDトークンの有効期間は1時間。境界付近でのリクエスト失敗を避けるため、
 * 余裕を持たせて50分でキャッシュを破棄し取り直す。
 */
const TOKEN_TTL_MS = 50 * 60 * 1000;

let cache: { audience: string; token: string; fetchedAt: number } | null = null;

/** `audience`（backendのURL）向けのGoogle IDトークンをメタデータサーバーから取得する。
 *
 * 呼び出し毎にメタデータサーバーへ問い合わせるとレイテンシが乗るため、audience単位で
 * プロセス内キャッシュする（このモジュールがimportされているNode.jsプロセス＝
 * frontendコンテナのインスタンス寿命の間だけ有効。複数インスタンス間では共有されないが、
 * インスタンス毎に取り直すだけなので問題ない）。
 */
const fetchGoogleIdToken = async (audience: string): Promise<string> => {
  if (cache && cache.audience === audience && Date.now() - cache.fetchedAt < TOKEN_TTL_MS) {
    return cache.token;
  }

  const url = `${METADATA_IDENTITY_URL}?audience=${encodeURIComponent(audience)}`;
  const response = await fetch(url, {
    headers: { "Metadata-Flavor": "Google" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Google IDトークンの取得に失敗しました（status=${response.status}）`);
  }

  const token = await response.text();
  cache = { audience, token, fetchedAt: Date.now() };
  return token;
};

/** backend呼び出し用のリクエストヘッダーを返す。
 *
 * `config.backendIdTokenEnabled`がfalseの環境（ローカル・compose・E2E）では何もせず空を返す。
 * trueの環境（Cloud Run、backendのIngressがIAM認証必須）でのみIDトークンを取得して
 * `Authorization: Bearer <token>`を付与する。
 */
export const backendAuthHeaders = async (): Promise<Record<string, string>> => {
  if (!config.backendIdTokenEnabled) {
    return {};
  }
  const token = await fetchGoogleIdToken(config.apiBaseUrl);
  return { Authorization: `Bearer ${token}` };
};

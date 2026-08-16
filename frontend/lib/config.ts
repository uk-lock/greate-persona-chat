import "server-only";

/** 環境変数から読み込むアプリケーション設定を一元管理する（frontend-typescript-react.md 論点2）。
 *
 * ここで扱う値はサーバー側（Server Component / Server Action）でのみ参照し、
 * `NEXT_PUBLIC_`プレフィックスは付けない（クライアントバンドルに含めない）。
 */
const requireEnv = (name: string): string => {
  const value = process.env[name];
  if (!value) {
    throw new Error(`環境変数 ${name} が設定されていません`);
  }
  return value;
};

export const config = {
  /** バックエンドAPIのベースURL（例：Docker Composeネットワーク内の `http://backend:8000`）。 */
  apiBaseUrl: requireEnv("API_BASE_URL"),
  /** セルフサインアップ機能の有効/無効フラグ（backend の SIGNUP_ENABLED と同じ値を想定）。 */
  signupEnabled: process.env.SIGNUP_ENABLED === "true",
};

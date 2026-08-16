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
  /** バックエンドAPIのベースURL（例：Docker Composeネットワーク内の `http://backend:8000`）。
   *
   * getterにして参照時まで評価を遅らせている。オブジェクトリテラルの通常プロパティにすると
   * `next build`のページデータ収集時（`config`をimportした瞬間）に即評価され、実行時にしか
   * 値が定まらない構成（同一イメージをstaging/prodへ使い回す等）でビルドが失敗するため
   * （frontend/Dockerfile.prod参照）。
   */
  get apiBaseUrl(): string {
    return requireEnv("API_BASE_URL");
  },
  /** セルフサインアップ機能の有効/無効フラグ（backend の SIGNUP_ENABLED と同じ値を想定）。 */
  get signupEnabled(): boolean {
    return process.env.SIGNUP_ENABLED === "true";
  },
};

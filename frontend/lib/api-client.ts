import "server-only";
import { config } from "./config";

/** バックエンドAPIがエラーレスポンス（`{"message": "string"}`）を返した場合の例外。 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiResult<T> = {
  data: T;
  /** レスポンスに含まれる `Set-Cookie` ヘッダー（複数件の可能性がある）。 */
  setCookie: string[];
};

type RequestOptions = {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  /** ブラウザから送られてきたCookieをそのままバックエンドへ転送する場合に指定する。 */
  cookie?: string;
};

/** バックエンドAPIを叩き、共通のエラー形式をApiErrorへ変換する薄いfetchラッパー（frontend-typescript-react.md 論点9）。 */
const request = async <T>(
  path: string,
  options: RequestOptions = {},
): Promise<ApiResult<T>> => {
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.cookie ? { Cookie: options.cookie } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as {
      message?: string;
    } | null;
    throw new ApiError(response.status, errorBody?.message ?? "エラーが発生しました");
  }

  const setCookie = response.headers.getSetCookie();
  const data = (await response.json().catch(() => undefined)) as T;
  return { data, setCookie };
};

export const apiClient = {
  get: <T>(path: string, cookie?: string) => request<T>(path, { cookie }),
  post: <T>(path: string, body?: unknown, cookie?: string) =>
    request<T>(path, { method: "POST", body, cookie }),
  delete: <T>(path: string, cookie?: string) =>
    request<T>(path, { method: "DELETE", cookie }),
};

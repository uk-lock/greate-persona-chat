import type { cookies } from "next/headers";

type CookieStore = Awaited<ReturnType<typeof cookies>>;

type ParsedCookie = {
  name: string;
  value: string;
  options: {
    path?: string;
    maxAge?: number;
    httpOnly?: boolean;
    secure?: boolean;
    sameSite?: "lax" | "strict" | "none";
  };
};

/** バックエンドの`Set-Cookie`ヘッダー1件を、Next.jsの`cookies().set()`へ渡せる形に分解する。
 *
 * Server Actionからのfetchはブラウザではなくバックエンドへ直接向くため、バックエンドが
 * 返す`Set-Cookie`はNext.jsサーバーへの応答にしか含まれない。ブラウザへCookieを届けるには、
 * この内容をNext.js側のレスポンスのCookieとして自前で設定し直す必要がある。
 */
export const parseSetCookie = (header: string): ParsedCookie | null => {
  const [pair, ...attributes] = header.split(";").map((part) => part.trim());
  const separatorIndex = pair.indexOf("=");
  if (separatorIndex === -1) {
    return null;
  }

  const name = pair.slice(0, separatorIndex);
  const value = pair.slice(separatorIndex + 1);
  const options: ParsedCookie["options"] = {};

  for (const attribute of attributes) {
    const [rawKey, rawValue] = attribute.split("=");
    switch (rawKey.trim().toLowerCase()) {
      case "path":
        options.path = rawValue;
        break;
      case "max-age":
        options.maxAge = Number(rawValue);
        break;
      case "httponly":
        options.httpOnly = true;
        break;
      case "secure":
        options.secure = true;
        break;
      case "samesite":
        options.sameSite = rawValue?.trim().toLowerCase() as ParsedCookie["options"]["sameSite"];
        break;
    }
  }

  return { name, value, options };
};

/** バックエンドの`Set-Cookie`ヘッダー群を、Next.jsのCookieStoreへそのまま反映する。 */
export const applySetCookies = (cookieStore: CookieStore, setCookieHeaders: string[]): void => {
  for (const header of setCookieHeaders) {
    const parsed = parseSetCookie(header);
    if (parsed) {
      cookieStore.set(parsed.name, parsed.value, parsed.options);
    }
  }
};

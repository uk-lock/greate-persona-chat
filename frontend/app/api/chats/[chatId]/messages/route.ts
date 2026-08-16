import { cookies } from "next/headers";
import { config } from "@/lib/config";
import { getAuthCookieHeader } from "@/lib/cookie";

type RouteParams = {
  params: Promise<{ chatId: string }>;
};

/** `POST /chats/{chat_id}/messages`のSSEレスポンスをブラウザへ中継するRoute Handler。
 *
 * バックエンド（`API_BASE_URL`、Docker Compose内部ホスト）はブラウザから直接到達できない。
 * `EventSource`はPOSTに対応しないため、クライアントは`fetch`でこのエンドポイントを呼び、
 * レスポンスのReadableStreamを自前でパースする（`_sse.ts`参照）。
 */
export const POST = async (request: Request, { params }: RouteParams): Promise<Response> => {
  const { chatId } = await params;
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);
  const body = await request.text();

  const backendResponse = await fetch(`${config.apiBaseUrl}/chats/${chatId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
    },
    body,
    signal: request.signal,
  });

  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: {
      "Content-Type": backendResponse.headers.get("Content-Type") ?? "application/json",
    },
  });
};

import { cookies } from "next/headers";
import { getAuthCookieHeader } from "@/lib/cookie";
import { ChatRoom } from "./_components/chat-room";
import { fetchChatDetail, fetchMessages } from "./_data";

type Props = {
  params: Promise<{ chatId: string }>;
};

/** S03 チャット画面（/chats/{chat_id}）。 */
const ChatPage = async ({ params }: Props) => {
  const { chatId } = await params;
  const cookieStore = await cookies();
  const cookieHeader = getAuthCookieHeader(cookieStore);

  const chatDetail = await fetchChatDetail(chatId, cookieHeader);
  const messages = await fetchMessages(chatId, cookieHeader);

  return <ChatRoom chatId={chatId} chatDetail={chatDetail} initialMessages={messages} />;
};

export default ChatPage;

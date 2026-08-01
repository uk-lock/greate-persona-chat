import { cookies } from "next/headers";
import { getAuthCookieHeader } from "@/lib/cookie";
import { ChatList } from "./_components/chat-list";
import { fetchChats } from "./_data";

/** S02 チャット履歴画面（/chats）。 */
const ChatsPage = async () => {
  const cookieStore = await cookies();
  const chats = await fetchChats(getAuthCookieHeader(cookieStore));

  return (
    <div className="flex flex-1 flex-col gap-6 px-8 py-10">
      <h1 className="font-display text-2xl font-bold tracking-wide text-heading">チャット履歴</h1>
      <ChatList initialChats={chats} />
    </div>
  );
};

export default ChatsPage;

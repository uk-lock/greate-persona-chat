import { cookies } from "next/headers";
import { getAuthCookieHeader } from "@/lib/cookie";
import { PersonaSelector } from "./_components/persona-selector";
import { fetchPersonaOptions } from "./_data";

type Props = {
  searchParams: Promise<{ persona_id?: string }>;
};

/** S01 新規チャット画面（/chats/new）。
 *
 * S05から「チャットを始める」で遷移した場合、`persona_id`クエリパラメータで対象ペルソナを
 * 事前選択する（S05-persona-detail.md 12節：遷移方式はURLクエリパラメータで実装）。
 */
const NewChatPage = async ({ searchParams }: Props) => {
  const { persona_id: personaIdParam } = await searchParams;
  const cookieStore = await cookies();
  const personas = await fetchPersonaOptions(getAuthCookieHeader(cookieStore));

  const requestedId = personaIdParam ? Number(personaIdParam) : null;
  const initialSelectedId = personas.some((persona) => persona.id === requestedId)
    ? requestedId
    : null;

  return (
    <div className="flex flex-1 flex-col gap-6 px-8 py-10">
      <h1 className="font-display text-2xl font-bold tracking-wide text-heading">新規チャット</h1>
      <PersonaSelector personas={personas} initialSelectedId={initialSelectedId} />
    </div>
  );
};

export default NewChatPage;

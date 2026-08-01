import { cookies } from "next/headers";
import { getAuthCookieHeader } from "@/lib/cookie";
import { PersonaList } from "./_components/persona-list";
import { fetchPersonas } from "./_data";

/** S04 ペルソナ一覧画面（/personas）。 */
const PersonasPage = async () => {
  const cookieStore = await cookies();
  const personas = await fetchPersonas(getAuthCookieHeader(cookieStore));

  return (
    <div className="flex flex-1 flex-col gap-6 px-8 py-10">
      <h1 className="font-display text-2xl font-bold tracking-wide text-heading">ペルソナ一覧</h1>
      <PersonaList personas={personas} />
    </div>
  );
};

export default PersonasPage;

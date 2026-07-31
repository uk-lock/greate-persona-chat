import Link from "next/link";
import { cookies } from "next/headers";
import { getAuthCookieHeader } from "@/lib/cookie";
import { fetchPersona } from "./_data";

type Props = {
  params: Promise<{ personaId: string }>;
};

/** S05 ペルソナ詳細画面（/personas/{persona_id}）。 */
const PersonaDetailPage = async ({ params }: Props) => {
  const { personaId } = await params;
  const cookieStore = await cookies();
  const persona = await fetchPersona(Number(personaId), getAuthCookieHeader(cookieStore));

  const basicInfo = [persona.country, persona.era].filter(Boolean).join("・");
  const hasQuotes = persona.sample_quotes !== null && persona.sample_quotes.length > 0;

  return (
    <div className="flex flex-1 flex-col">
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-surface-border bg-background/95 px-8 py-4">
        <Link href="/personas" className="text-sm text-muted hover:text-gold">
          ← 一覧に戻る
        </Link>
        <Link
          href={`/chats/new?persona_id=${persona.id}`}
          className="rounded-sm border border-gold bg-wine px-5 py-2 font-display text-sm tracking-wide text-foreground hover:bg-wine-bright"
        >
          チャットを始める
        </Link>
      </div>

      <div className="flex flex-col gap-8 px-8 py-10">
        <div className="flex flex-col items-center gap-4 text-center">
          {persona.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element -- 外部URL（Wikimedia Commons等）を再ホストせずそのまま表示する方針（20260728 steering参照）
            <img
              src={persona.image_url}
              alt={persona.name}
              className="h-48 w-48 rounded-full object-cover"
            />
          ) : (
            <span
              aria-hidden="true"
              className="flex h-48 w-48 items-center justify-center rounded-full bg-surface-border text-6xl text-muted"
            >
              {persona.name.slice(0, 1)}
            </span>
          )}
          <h1 className="font-display text-3xl tracking-wide text-gold">{persona.name}</h1>
          {basicInfo && <p className="text-sm text-muted">{basicInfo}</p>}
        </div>

        {persona.summary && (
          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg text-gold">概要</h2>
            <p className="whitespace-pre-wrap text-foreground">{persona.summary}</p>
          </section>
        )}

        {persona.description && (
          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg text-gold">詳細説明</h2>
            <p className="whitespace-pre-wrap text-foreground">{persona.description}</p>
          </section>
        )}

        {persona.personality && (
          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg text-gold">性格</h2>
            <p className="whitespace-pre-wrap text-foreground">{persona.personality}</p>
          </section>
        )}

        {persona.biography && (
          <section className="flex flex-col gap-2">
            <h2 className="font-display text-lg text-gold">経歴</h2>
            <p className="whitespace-pre-wrap text-foreground">{persona.biography}</p>
          </section>
        )}

        {hasQuotes && (
          <section className="flex flex-col gap-3">
            <h2 className="font-display text-lg text-gold">発言例</h2>
            <ul className="flex flex-col gap-3">
              {persona.sample_quotes?.map((quote, index) => (
                <li
                  key={index}
                  className="border-l-2 border-gold pl-4 text-foreground italic"
                >
                  「{quote}」
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
};

export default PersonaDetailPage;

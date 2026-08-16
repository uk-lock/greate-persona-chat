"use client";

import { useState } from "react";
import Link from "next/link";
import { truncateSummary } from "../_format";
import type { PersonaSummary } from "../_types";

type Props = {
  personas: PersonaSummary[];
};

const inputClassName =
  "w-full max-w-sm rounded-sm border border-surface-border bg-surface px-3 py-2 text-foreground placeholder:text-muted focus:border-gold focus:outline-none";

/** S04 ペルソナ一覧画面のリスト本体（Client Component）。ペルソナ名でのリアルタイム絞り込みを持つ。 */
export const PersonaList = ({ personas }: Props) => {
  const [keyword, setKeyword] = useState("");

  if (personas.length === 0) {
    return <p className="text-muted">ペルソナが登録されていません。</p>;
  }

  const filteredPersonas = personas.filter((persona) =>
    persona.name.toLowerCase().includes(keyword.toLowerCase()),
  );

  return (
    <div className="flex flex-col gap-6">
      <label className="flex flex-col gap-1.5">
        <span className="font-display text-sm tracking-wide text-gold">ペルソナ名で検索</span>
        <input
          type="text"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="例：織田信長"
          className={inputClassName}
        />
      </label>

      {filteredPersonas.length === 0 ? (
        <p className="text-muted">該当するペルソナが見つかりません</p>
      ) : (
        <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {filteredPersonas.map((persona) => (
            <li key={persona.id}>
              <Link
                href={`/personas/${persona.id}`}
                className="flex h-full flex-col gap-3 rounded-md border border-surface-border bg-surface p-4 transition-colors hover:border-gold"
              >
                {persona.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element -- 外部URL（Wikimedia Commons等）を再ホストせずそのまま表示する方針（20260728 steering参照）
                  <img
                    src={persona.image_url}
                    alt={persona.name}
                    className="aspect-square w-full rounded-sm object-cover"
                  />
                ) : (
                  <span
                    aria-hidden="true"
                    className="flex aspect-square w-full items-center justify-center rounded-sm bg-surface-border text-2xl text-muted"
                  >
                    {persona.name.slice(0, 1)}
                  </span>
                )}
                <p className="font-display text-foreground">{persona.name}</p>
                <p className="text-sm text-muted">{truncateSummary(persona.summary)}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

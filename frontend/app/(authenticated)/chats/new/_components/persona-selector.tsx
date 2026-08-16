"use client";

import { useState } from "react";
import {
  CHAT_PERSONA_MAX_COUNT,
  CHAT_PERSONA_MIN_COUNT,
  CHAT_TOPIC_MAX_LENGTH,
} from "@/lib/constants";
import { createChatAction } from "../_actions";
import type { ChatMode, PersonaOption } from "../_types";

type Props = {
  personas: PersonaOption[];
  initialSelectedId: number | null;
};

const inputClassName =
  "w-full max-w-sm rounded-sm border border-surface-border bg-surface px-3 py-2 text-foreground placeholder:text-muted focus:border-gold focus:outline-none";

/** S01 新規チャット画面のペルソナ選択・チャットモード選択・開始ボタンをまとめたClient Component。 */
export const PersonaSelector = ({ personas, initialSelectedId }: Props) => {
  const [selectedIds, setSelectedIds] = useState<number[]>(
    initialSelectedId !== null ? [initialSelectedId] : [],
  );
  const [keyword, setKeyword] = useState("");
  const [chatMode, setChatMode] = useState<ChatMode>("USER_PARTICIPATED");
  const [topic, setTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const isAtMax = selectedIds.length >= CHAT_PERSONA_MAX_COUNT;
  const isPersonaOnly = chatMode === "PERSONA_ONLY";
  const trimmedTopic = topic.trim();
  const canSubmit =
    !isSubmitting &&
    personas.length > 0 &&
    selectedIds.length >= CHAT_PERSONA_MIN_COUNT &&
    selectedIds.length <= CHAT_PERSONA_MAX_COUNT &&
    (!isPersonaOnly || trimmedTopic.length > 0);

  const toggleSelect = (personaId: number) => {
    setSelectedIds((prev) => {
      if (prev.includes(personaId)) {
        return prev.filter((id) => id !== personaId);
      }
      if (prev.length >= CHAT_PERSONA_MAX_COUNT) {
        return prev;
      }
      return [...prev, personaId];
    });
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setFormError(null);
    const result = await createChatAction(
      selectedIds,
      chatMode,
      isPersonaOnly ? trimmedTopic : undefined,
    );
    setIsSubmitting(false);
    if (result?.error) {
      setFormError(result.error);
    }
  };

  if (personas.length === 0) {
    return <p className="text-muted">選択可能なペルソナがありません。</p>;
  }

  const selectedPersonas = personas.filter((persona) => selectedIds.includes(persona.id));
  const filteredPersonas = personas.filter((persona) =>
    persona.name.toLowerCase().includes(keyword.toLowerCase()),
  );

  return (
    <div className="flex flex-col gap-6">
      {formError && (
        <p
          role="alert"
          className="rounded-sm border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger-text"
        >
          {formError}
        </p>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="font-display text-sm tracking-wide text-gold">
          選択中のペルソナ（{selectedIds.length}/{CHAT_PERSONA_MAX_COUNT}体選択中）
        </h2>
        {selectedPersonas.length === 0 ? (
          <p className="text-sm text-muted">
            ペルソナを{CHAT_PERSONA_MIN_COUNT}体以上選択してください。
          </p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {selectedPersonas.map((persona) => (
              <li
                key={persona.id}
                className="flex items-center gap-2 rounded-full border border-gold bg-wine/40 py-1 pl-3 pr-2 text-sm text-foreground"
              >
                {persona.name}
                <button
                  type="button"
                  aria-label={`${persona.name}の選択を解除`}
                  disabled={isSubmitting}
                  onClick={() => toggleSelect(persona.id)}
                  className="flex h-5 w-5 items-center justify-center rounded-full text-muted hover:text-gold disabled:opacity-50"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <label className="flex flex-col gap-1.5">
        <span className="font-display text-sm tracking-wide text-gold">ペルソナ名で検索</span>
        <input
          type="text"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="例：織田信長"
          disabled={isSubmitting}
          className={inputClassName}
        />
      </label>

      {filteredPersonas.length === 0 ? (
        <p className="text-muted">該当するペルソナが見つかりません</p>
      ) : (
        <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {filteredPersonas.map((persona) => {
            const isSelected = selectedIds.includes(persona.id);
            const isDisabled = isSubmitting || (!isSelected && isAtMax);
            return (
              <li key={persona.id}>
                <button
                  type="button"
                  aria-pressed={isSelected}
                  disabled={isDisabled}
                  onClick={() => toggleSelect(persona.id)}
                  className={`relative flex w-full flex-col gap-2 rounded-md border p-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                    isSelected
                      ? "border-gold bg-wine/40"
                      : "border-surface-border bg-surface hover:border-gold"
                  }`}
                >
                  {isSelected && (
                    <span
                      aria-hidden="true"
                      className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-gold text-xs text-background"
                    >
                      ✓
                    </span>
                  )}
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
                  <p className="text-sm text-foreground">{persona.name}</p>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <fieldset className="flex flex-col gap-2" disabled={isSubmitting}>
        <legend className="font-display text-sm tracking-wide text-gold">チャットモード</legend>
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="radio"
            name="chat_mode"
            value="USER_PARTICIPATED"
            checked={chatMode === "USER_PARTICIPATED"}
            onChange={() => setChatMode("USER_PARTICIPATED")}
          />
          あなたも参加する
        </label>
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="radio"
            name="chat_mode"
            value="PERSONA_ONLY"
            checked={chatMode === "PERSONA_ONLY"}
            onChange={() => setChatMode("PERSONA_ONLY")}
          />
          ペルソナ同士の会話を観る
        </label>
      </fieldset>

      {isPersonaOnly && (
        <div className="flex flex-col gap-1.5">
          <label className="flex flex-col gap-1.5">
            <span className="font-display text-sm tracking-wide text-gold">会話のお題（必須）</span>
            <input
              type="text"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="例：理想のリーダーシップとは"
              maxLength={CHAT_TOPIC_MAX_LENGTH}
              disabled={isSubmitting}
              className={inputClassName}
            />
          </label>
          <span className="text-xs text-muted">
            ペルソナ同士の会話はここで入力したお題に沿って進みます。
          </span>
        </div>
      )}

      <button
        type="button"
        disabled={!canSubmit}
        onClick={handleSubmit}
        className="self-start rounded-sm border border-gold bg-wine px-6 py-2.5 font-display tracking-widest text-on-accent transition-colors hover:bg-wine-bright disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "作成中…" : "チャット開始"}
      </button>
    </div>
  );
};

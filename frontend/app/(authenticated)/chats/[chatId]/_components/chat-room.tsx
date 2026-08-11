"use client";

import { useEffect, useRef, useState } from "react";
import { stopChatAction } from "../_actions";
import { MessageStreamError, startMessageStream } from "../_sse";
import type { ChatDetail, ChatMessage, ChatStreamEvent, Participant } from "../_types";

type Props = {
  chatId: string;
  chatDetail: ChatDetail;
  initialMessages: ChatMessage[];
};

const MESSAGE_MAX_LENGTH = 500;

/** S03 チャット画面の本体（Client Component）。メッセージ送受信・SSE購読・状態遷移を管理する。 */
export const ChatRoom = ({ chatId, chatDetail, initialMessages }: Props) => {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [title, setTitle] = useState(chatDetail.title);
  const [isGenerating, setIsGenerating] = useState(false);
  const [thinkingPersonaId, setThinkingPersonaId] = useState<number | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStreamEvent = (event: ChatStreamEvent) => {
    switch (event.type) {
      case "thinking":
        setThinkingPersonaId(event.persona_id);
        break;
      case "message":
        setMessages((prev) => [...prev, event.message]);
        setThinkingPersonaId(null);
        break;
      case "title":
        setTitle(event.title);
        break;
      case "error":
        setFormError(event.message);
        setThinkingPersonaId(null);
        break;
    }
  };

  const runStream = async (body: { message?: string }) => {
    setFormError(null);
    setIsGenerating(true);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await startMessageStream(chatId, body, controller.signal, handleStreamEvent);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        // ユーザーが停止操作を行った場合。エラー表示はしない。
      } else if (error instanceof MessageStreamError) {
        setFormError(error.message);
      } else {
        setFormError("通信エラーが発生しました。時間をおいて再度お試しください。");
      }
    } finally {
      setIsGenerating(false);
      setThinkingPersonaId(null);
      abortControllerRef.current = null;
    }
  };

  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isGenerating) {
      return;
    }
    setInputValue("");
    void runStream({ message: trimmed });
  };

  const handleStart = () => {
    if (isGenerating) {
      return;
    }
    void runStream({});
  };

  const handleStop = async () => {
    abortControllerRef.current?.abort();
    const result = await stopChatAction(chatId);
    if (result?.error) {
      setFormError(result.error);
    }
  };

  const findParticipant = (personaId: number | null): Participant | undefined => {
    if (personaId === null) {
      return chatDetail.participants.find((participant) => participant.type === "USER");
    }
    return chatDetail.participants.find(
      (participant) => participant.type === "PERSONA" && participant.persona_id === personaId,
    );
  };

  const emptyText =
    chatDetail.chat_mode === "USER_PARTICIPATED"
      ? "メッセージを送ってみましょう"
      : "開始ボタンを押して会話を始めましょう";

  return (
    <div className="flex flex-1 flex-col min-h-0">
      <header className="sticky top-0 z-10 flex flex-col gap-1 border-b border-surface-border bg-background/95 px-8 py-4">
        <div className="flex items-center gap-3">
          <h1 className="font-display text-lg font-bold text-heading">{title}</h1>
          <div className="flex items-center gap-2">
            {chatDetail.participants.map((participant, index) =>
              participant.type === "USER" ? (
                <span key={`user-${index}`} className="text-sm text-muted">
                  あなた
                </span>
              ) : (
                <ParticipantAvatar key={participant.persona_id} participant={participant} />
              ),
            )}
          </div>
        </div>
        {chatDetail.topic && (
          <p className="text-sm text-muted">お題：{chatDetail.topic}</p>
        )}
      </header>

      <div className="flex flex-1 min-h-0 flex-col gap-4 overflow-y-auto px-8 py-6">
        {messages.length === 0 && !isGenerating ? (
          <p className="text-muted">{emptyText}</p>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              participant={findParticipant(message.persona_id)}
            />
          ))
        )}
        {isGenerating && (
          <p className="text-sm text-muted" aria-live="polite">
            {thinkingPersonaId !== null
              ? `${findParticipant(thinkingPersonaId)?.name ?? ""}が考え中…`
              : "…"}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      {formError && (
        <p
          role="alert"
          className="mx-8 mb-4 rounded-sm border border-danger-border bg-danger-bg px-4 py-3 text-sm text-danger-text"
        >
          {formError}
        </p>
      )}

      <div className="border-t border-surface-border px-8 py-4">
        {chatDetail.chat_mode === "USER_PARTICIPATED" ? (
          <div className="flex items-end gap-3">
            <textarea
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              maxLength={MESSAGE_MAX_LENGTH}
              disabled={isGenerating}
              placeholder="メッセージを入力"
              rows={2}
              className="flex-1 rounded-sm border border-surface-border bg-surface px-3 py-2 text-foreground placeholder:text-muted focus:border-gold focus:outline-none disabled:opacity-50"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={isGenerating || inputValue.trim().length === 0}
              className="rounded-sm border border-gold bg-wine px-5 py-2 text-sm text-on-accent hover:bg-wine-bright disabled:cursor-not-allowed disabled:opacity-60"
            >
              送信
            </button>
            <button
              type="button"
              onClick={handleStop}
              disabled={!isGenerating}
              className="rounded-sm border border-surface-border px-5 py-2 text-sm text-muted hover:text-gold disabled:cursor-not-allowed disabled:opacity-40"
            >
              停止
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleStart}
              disabled={isGenerating}
              className="rounded-sm border border-gold bg-wine px-5 py-2 text-sm text-on-accent hover:bg-wine-bright disabled:cursor-not-allowed disabled:opacity-60"
            >
              開始
            </button>
            <button
              type="button"
              onClick={handleStop}
              disabled={!isGenerating}
              className="rounded-sm border border-surface-border px-5 py-2 text-sm text-muted hover:text-gold disabled:cursor-not-allowed disabled:opacity-40"
            >
              停止
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const ParticipantAvatar = ({
  participant,
}: {
  participant: Extract<Participant, { type: "PERSONA" }>;
}) => {
  return participant.image_url ? (
    // eslint-disable-next-line @next/next/no-img-element -- 外部URL（Wikimedia Commons等）を再ホストせずそのまま表示する方針（20260728 steering参照）
    <img
      src={participant.image_url}
      alt={participant.name}
      title={participant.name}
      className="h-8 w-8 rounded-full object-cover"
    />
  ) : (
    <span
      title={participant.name}
      aria-label={participant.name}
      className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-border text-xs text-muted"
    >
      {participant.name.slice(0, 1)}
    </span>
  );
};

const MessageBubble = ({
  message,
  participant,
}: {
  message: ChatMessage;
  participant: Participant | undefined;
}) => {
  const isUser = message.speaker_type === "USER";
  const name = participant?.name ?? (isUser ? "あなた" : "");

  return (
    <div className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
      <span className="text-xs text-muted">{name}</span>
      <p
        className={`max-w-lg whitespace-pre-wrap rounded-md px-4 py-2 text-sm ${
          isUser
            ? "bg-user-bubble-bg text-foreground"
            : "border border-surface-border bg-surface text-foreground"
        }`}
      >
        {message.message}
      </p>
    </div>
  );
};

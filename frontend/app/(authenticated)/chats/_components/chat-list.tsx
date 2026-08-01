"use client";

import { useState } from "react";
import Link from "next/link";
import { deleteChatAction } from "../_actions";
import { formatUpdatedAt } from "../_format";
import type { Chat, Participant } from "../_types";

type Props = {
  initialChats: Chat[];
};

/** S02 チャット履歴画面のリスト本体（Client Component）。削除確認ダイアログの状態を持つ。 */
export const ChatList = ({ initialChats }: Props) => {
  const [chats, setChats] = useState(initialChats);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const closeDialog = () => {
    setPendingDeleteId(null);
    setDeleteError(null);
  };

  const handleConfirmDelete = async () => {
    if (pendingDeleteId === null) {
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);
    const result = await deleteChatAction(pendingDeleteId);
    setIsDeleting(false);
    if (result?.error) {
      setDeleteError(result.error);
      return;
    }
    setChats((prev) => prev.filter((chat) => chat.chat_id !== pendingDeleteId));
    setPendingDeleteId(null);
  };

  if (chats.length === 0) {
    return <p className="text-muted">まだチャットがありません。新規チャットから会話を始めましょう。</p>;
  }

  return (
    <>
      <ul className="flex flex-col gap-3">
        {chats.map((chat) => (
          <li
            key={chat.chat_id}
            className="flex items-center justify-between gap-4 rounded-sm border border-surface-border bg-surface px-5 py-4"
          >
            <div className="flex flex-col gap-2">
              <p className="font-display text-lg text-foreground">{chat.title}</p>
              <div className="flex flex-wrap items-center gap-3">
                {chat.participants.map((participant, index) => (
                  <ParticipantBadge key={`${chat.chat_id}-${index}`} participant={participant} />
                ))}
              </div>
              <p className="text-sm text-muted">{formatUpdatedAt(chat.updated_at)}</p>
            </div>

            <div className="flex items-center gap-2">
              <Link
                href={`/chats/${chat.chat_id}`}
                className="rounded-sm border border-gold px-4 py-2 text-sm text-gold hover:bg-wine/40"
              >
                Open
              </Link>
              <button
                type="button"
                aria-label={`${chat.title}を削除`}
                onClick={() => setPendingDeleteId(chat.chat_id)}
                className="flex h-9 w-9 items-center justify-center rounded-sm text-muted hover:bg-danger-bg hover:text-danger-text"
              >
                <DeleteIcon />
              </button>
            </div>
          </li>
        ))}
      </ul>

      {pendingDeleteId !== null && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/60">
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
            className="w-full max-w-sm rounded-md border border-surface-border bg-surface p-6"
          >
            <p id="delete-dialog-title" className="mb-4 text-foreground">
              このチャットを削除しますか？
            </p>
            {deleteError && (
              <p role="alert" className="mb-4 text-sm text-danger-text">
                {deleteError}
              </p>
            )}
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={closeDialog}
                disabled={isDeleting}
                className="rounded-sm border border-surface-border px-4 py-2 text-sm text-muted disabled:opacity-50"
              >
                キャンセル
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="rounded-sm border border-gold bg-wine px-4 py-2 text-sm text-on-accent disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isDeleting ? "削除中…" : "OK"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const ParticipantBadge = ({ participant }: { participant: Participant }) => {
  if (participant.type === "USER") {
    return <span className="text-sm text-gold">{participant.name}</span>;
  }

  return (
    <span className="flex items-center gap-1.5 text-sm text-foreground">
      {participant.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element -- Wikimedia Commons等の外部URLを再ホストしないため画像最適化を使わない方針（20260728 steering参照）
        <img
          src={participant.image_url}
          alt={participant.name}
          className="h-6 w-6 rounded-full object-cover"
        />
      ) : (
        <span
          aria-hidden="true"
          className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-border text-xs text-muted"
        >
          {participant.name.slice(0, 1)}
        </span>
      )}
      {participant.name}
    </span>
  );
};

const DeleteIcon = () => {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path
        d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-8 0 1 12a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2l1-12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

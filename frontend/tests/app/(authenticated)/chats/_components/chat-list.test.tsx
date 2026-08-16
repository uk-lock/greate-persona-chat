import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatList } from "@/app/(authenticated)/chats/_components/chat-list";
import { deleteChatAction } from "@/app/(authenticated)/chats/_actions";
import type { Chat } from "@/app/(authenticated)/chats/_types";

vi.mock("@/app/(authenticated)/chats/_actions", () => ({
  deleteChatAction: vi.fn(),
}));

const mockedDeleteChatAction = vi.mocked(deleteChatAction);

const CHAT_ID = "11111111-1111-1111-1111-111111111111";

const buildChats = (): Chat[] => [
  {
    chat_id: CHAT_ID,
    title: "歴史談義",
    chat_mode: "USER_PARTICIPATED",
    updated_at: "2026-07-30T09:00:00+09:00",
    participants: [
      { type: "USER", name: "あなた" },
      { type: "PERSONA", persona_id: 10, name: "織田信長", image_url: null },
    ],
  },
];

describe("ChatList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("チャットが0件の場合は案内文言のみを表示する", () => {
    render(<ChatList initialChats={[]} />);

    expect(
      screen.getByText("まだチャットがありません。新規チャットから会話を始めましょう。"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open" })).not.toBeInTheDocument();
  });

  test("チャット一覧と参加者を表示する", () => {
    render(<ChatList initialChats={buildChats()} />);

    expect(screen.getByText("歴史談義")).toBeInTheDocument();
    expect(screen.getByText("あなた")).toBeInTheDocument();
    expect(screen.getByText("織田信長")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open" })).toHaveAttribute("href", `/chats/${CHAT_ID}`);
  });

  test("削除ボタン押下で確認ダイアログを表示し、OKで削除してリストから消す", async () => {
    mockedDeleteChatAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<ChatList initialChats={buildChats()} />);

    await user.click(screen.getByRole("button", { name: "歴史談義を削除" }));
    expect(screen.getByText("このチャットを削除しますか？")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "OK" }));

    expect(mockedDeleteChatAction).toHaveBeenCalledWith(CHAT_ID);
    expect(
      await screen.findByText("まだチャットがありません。新規チャットから会話を始めましょう。"),
    ).toBeInTheDocument();
  });

  test("キャンセル押下ではdeleteChatActionを呼ばずダイアログを閉じる", async () => {
    const user = userEvent.setup();
    render(<ChatList initialChats={buildChats()} />);

    await user.click(screen.getByRole("button", { name: "歴史談義を削除" }));
    await user.click(screen.getByRole("button", { name: "キャンセル" }));

    expect(screen.queryByText("このチャットを削除しますか？")).not.toBeInTheDocument();
    expect(mockedDeleteChatAction).not.toHaveBeenCalled();
    expect(screen.getByText("歴史談義")).toBeInTheDocument();
  });

  test("削除失敗時はエラーメッセージを表示し、一覧は残す", async () => {
    mockedDeleteChatAction.mockResolvedValueOnce({
      error: "削除に失敗しました。時間をおいて再度お試しください。",
    });
    const user = userEvent.setup();
    render(<ChatList initialChats={buildChats()} />);

    await user.click(screen.getByRole("button", { name: "歴史談義を削除" }));
    await user.click(screen.getByRole("button", { name: "OK" }));

    expect(
      await screen.findByText("削除に失敗しました。時間をおいて再度お試しください。"),
    ).toBeInTheDocument();
    expect(screen.getByText("歴史談義")).toBeInTheDocument();
  });
});

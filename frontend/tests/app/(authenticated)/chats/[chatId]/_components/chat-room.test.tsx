import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatRoom } from "@/app/(authenticated)/chats/[chatId]/_components/chat-room";
import { stopChatAction } from "@/app/(authenticated)/chats/[chatId]/_actions";
import { startMessageStream } from "@/app/(authenticated)/chats/[chatId]/_sse";
import type { ChatDetail, ChatMessage } from "@/app/(authenticated)/chats/[chatId]/_types";

vi.mock("@/app/(authenticated)/chats/[chatId]/_actions", () => ({
  stopChatAction: vi.fn(),
}));

vi.mock("@/app/(authenticated)/chats/[chatId]/_sse", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/app/(authenticated)/chats/[chatId]/_sse")>();
  return {
    ...actual,
    startMessageStream: vi.fn(),
  };
});

const mockedStopChatAction = vi.mocked(stopChatAction);
const mockedStartMessageStream = vi.mocked(startMessageStream);

const CHAT_ID = "11111111-1111-1111-1111-111111111111";

const userParticipatedChat: ChatDetail = {
  chat_id: CHAT_ID,
  title: "歴史談義",
  chat_mode: "USER_PARTICIPATED",
  updated_at: "2026-07-30T09:00:00+09:00",
  participants: [
    { type: "USER", name: "あなた" },
    { type: "PERSONA", persona_id: 10, name: "織田信長", image_url: null },
  ],
};

const personaOnlyChat: ChatDetail = {
  ...userParticipatedChat,
  chat_mode: "PERSONA_ONLY",
  participants: [{ type: "PERSONA", persona_id: 10, name: "織田信長", image_url: null }],
};

const replyMessage: ChatMessage = {
  id: 2,
  sort_no: 2,
  speaker_type: "PERSONA",
  persona_id: 10,
  message: "是非に及ばず",
  created_at: "2026-07-30T09:01:00+09:00",
};

describe("ChatRoom", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("USER_PARTICIPATEDでメッセージが0件の場合は案内文言を表示する", () => {
    render(<ChatRoom chatId={CHAT_ID} chatDetail={userParticipatedChat} initialMessages={[]} />);

    expect(screen.getByText("メッセージを送ってみましょう")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("メッセージを入力")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "停止" })).toBeDisabled();
  });

  test("PERSONA_ONLYでメッセージが0件の場合は案内文言を表示し、入力欄は無い", () => {
    render(<ChatRoom chatId={CHAT_ID} chatDetail={personaOnlyChat} initialMessages={[]} />);

    expect(screen.getByText("開始ボタンを押して会話を始めましょう")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("メッセージを入力")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "開始" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "停止" })).toBeDisabled();
  });

  test("送信するとstartMessageStreamを呼び、受信したメッセージを吹き出しとして追加する", async () => {
    mockedStartMessageStream.mockImplementationOnce(async (_chatId, _body, _signal, onMessage) => {
      onMessage(replyMessage);
    });
    const user = userEvent.setup();
    render(<ChatRoom chatId={CHAT_ID} chatDetail={userParticipatedChat} initialMessages={[]} />);

    await user.type(screen.getByPlaceholderText("メッセージを入力"), "こんにちは");
    await user.click(screen.getByRole("button", { name: "送信" }));

    expect(mockedStartMessageStream).toHaveBeenCalledWith(
      CHAT_ID,
      { message: "こんにちは" },
      expect.any(AbortSignal),
      expect.any(Function),
    );
    expect(await screen.findByText("是非に及ばず")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("メッセージを入力")).toHaveValue("");
  });

  test("送信中は入力欄・送信ボタンが無効化され、停止ボタンが有効になる", async () => {
    let resolveStream: () => void = () => {};
    mockedStartMessageStream.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveStream = () => resolve(undefined);
        }),
    );
    const user = userEvent.setup();
    render(<ChatRoom chatId={CHAT_ID} chatDetail={userParticipatedChat} initialMessages={[]} />);

    await user.type(screen.getByPlaceholderText("メッセージを入力"), "こんにちは");
    await user.click(screen.getByRole("button", { name: "送信" }));

    expect(screen.getByPlaceholderText("メッセージを入力")).toBeDisabled();
    expect(screen.getByRole("button", { name: "送信" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "停止" })).toBeEnabled();

    resolveStream();
    await screen.findByRole("button", { name: "停止" });
    expect(screen.getByRole("button", { name: "停止" })).toBeDisabled();
  });

  test("停止ボタン押下でstopChatActionを呼び出す", async () => {
    let resolveStream: () => void = () => {};
    mockedStartMessageStream.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveStream = () => resolve(undefined);
        }),
    );
    mockedStopChatAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<ChatRoom chatId={CHAT_ID} chatDetail={personaOnlyChat} initialMessages={[]} />);

    await user.click(screen.getByRole("button", { name: "開始" }));
    await user.click(screen.getByRole("button", { name: "停止" }));

    expect(mockedStopChatAction).toHaveBeenCalledWith(CHAT_ID);
    resolveStream();
  });

  test("送信エラー時はエラーメッセージを表示する", async () => {
    const { MessageStreamError } = await import("@/app/(authenticated)/chats/[chatId]/_sse");
    mockedStartMessageStream.mockRejectedValueOnce(
      new MessageStreamError("リクエストが多すぎます。しばらくしてから再度お試しください。"),
    );
    const user = userEvent.setup();
    render(<ChatRoom chatId={CHAT_ID} chatDetail={userParticipatedChat} initialMessages={[]} />);

    await user.type(screen.getByPlaceholderText("メッセージを入力"), "こんにちは");
    await user.click(screen.getByRole("button", { name: "送信" }));

    expect(
      await screen.findByText("リクエストが多すぎます。しばらくしてから再度お試しください。"),
    ).toBeInTheDocument();
  });

  test("初期メッセージを発言者ごとに左右寄せで表示する", () => {
    const initialMessages: ChatMessage[] = [
      {
        id: 1,
        sort_no: 1,
        speaker_type: "USER",
        persona_id: null,
        message: "こんにちは",
        created_at: "2026-07-30T09:00:00+09:00",
      },
      replyMessage,
    ];
    render(
      <ChatRoom chatId={CHAT_ID} chatDetail={userParticipatedChat} initialMessages={initialMessages} />,
    );

    expect(screen.getByText("こんにちは")).toBeInTheDocument();
    expect(screen.getByText("是非に及ばず")).toBeInTheDocument();
    expect(screen.getByText("織田信長")).toBeInTheDocument();
  });
});

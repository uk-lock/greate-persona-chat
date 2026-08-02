import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PersonaSelector } from "@/app/(authenticated)/chats/new/_components/persona-selector";
import { createChatAction } from "@/app/(authenticated)/chats/new/_actions";
import type { PersonaOption } from "@/app/(authenticated)/chats/new/_types";

vi.mock("@/app/(authenticated)/chats/new/_actions", () => ({
  createChatAction: vi.fn(),
}));

const mockedCreateChatAction = vi.mocked(createChatAction);

const buildPersonas = (count: number): PersonaOption[] =>
  Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    name: `ペルソナ${index + 1}`,
    image_url: null,
    summary: null,
  }));

describe("PersonaSelector", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  test("ペルソナが0件の場合は案内文言のみを表示する", () => {
    render(<PersonaSelector personas={[]} initialSelectedId={null} />);

    expect(screen.getByText("選択可能なペルソナがありません。")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "チャット開始" })).not.toBeInTheDocument();
  });

  test("初期状態では開始ボタンが無効", () => {
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    expect(screen.getByRole("button", { name: "チャット開始" })).toBeDisabled();
  });

  test("ペルソナをクリックすると選択済み一覧に追加され、開始ボタンが有効になる", async () => {
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));

    expect(screen.getByText("選択中のペルソナ（1/5体選択中）")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ペルソナ1の選択を解除" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "チャット開始" })).toBeEnabled();
  });

  test("×マークで選択を解除できる", async () => {
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));
    await user.click(screen.getByRole("button", { name: "ペルソナ1の選択を解除" }));

    expect(screen.getByText("選択中のペルソナ（0/5体選択中）")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "チャット開始" })).toBeDisabled();
  });

  test("上限まで選択すると未選択のカードが無効化される", async () => {
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(6)} initialSelectedId={null} />);

    for (let i = 1; i <= 5; i += 1) {
      await user.click(screen.getByRole("button", { name: `ペルソナ${i}` }));
    }

    expect(screen.getByText("選択中のペルソナ（5/5体選択中）")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ペルソナ6" })).toBeDisabled();
  });

  test("検索欄に入力すると選択可能な一覧が絞り込まれる", async () => {
    const user = userEvent.setup();
    const personas = [
      { id: 1, name: "織田信長", image_url: null, summary: null },
      { id: 2, name: "豊臣秀吉", image_url: null, summary: null },
    ];
    render(<PersonaSelector personas={personas} initialSelectedId={null} />);

    await user.type(screen.getByLabelText("ペルソナ名で検索"), "信長");

    expect(screen.getByRole("button", { name: "織田信長" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "豊臣秀吉" })).not.toBeInTheDocument();
  });

  test("initialSelectedIdが渡された場合は事前選択される", () => {
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={2} />);

    expect(screen.getByText("選択中のペルソナ（1/5体選択中）")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ペルソナ2の選択を解除" })).toBeInTheDocument();
  });

  test("チャット開始ボタン押下でcreateChatActionを呼び出す", async () => {
    mockedCreateChatAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));
    await user.click(screen.getByRole("button", { name: "チャット開始" }));

    expect(mockedCreateChatAction).toHaveBeenCalledWith([1], "USER_PARTICIPATED", undefined);
  });

  test("PERSONA_ONLYではお題が未入力の間は開始ボタンが無効", async () => {
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));
    await user.click(screen.getByRole("radio", { name: "ペルソナ同士の会話を観る" }));

    expect(screen.getByRole("button", { name: "チャット開始" })).toBeDisabled();
  });

  test("PERSONA_ONLYでお題を入力するとcreateChatActionへtopicを渡す", async () => {
    mockedCreateChatAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));
    await user.click(screen.getByRole("radio", { name: "ペルソナ同士の会話を観る" }));
    await user.type(screen.getByLabelText("会話のお題（必須）"), "理想のリーダーシップとは");
    await user.click(screen.getByRole("button", { name: "チャット開始" }));

    expect(mockedCreateChatAction).toHaveBeenCalledWith(
      [1],
      "PERSONA_ONLY",
      "理想のリーダーシップとは",
    );
  });

  test("作成失敗時はエラーメッセージを表示し、選択状態を保持する", async () => {
    mockedCreateChatAction.mockResolvedValueOnce({ error: "チャットの作成に失敗しました。" });
    const user = userEvent.setup();
    render(<PersonaSelector personas={buildPersonas(3)} initialSelectedId={null} />);

    await user.click(screen.getByRole("button", { name: "ペルソナ1" }));
    await user.click(screen.getByRole("button", { name: "チャット開始" }));

    expect(await screen.findByText("チャットの作成に失敗しました。")).toBeInTheDocument();
    expect(screen.getByText("選択中のペルソナ（1/5体選択中）")).toBeInTheDocument();
  });
});

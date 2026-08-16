import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PersonaList } from "@/app/(authenticated)/personas/_components/persona-list";
import type { PersonaSummary } from "@/app/(authenticated)/personas/_types";

const buildPersonas = (): PersonaSummary[] => [
  { id: 1, name: "織田信長", image_url: null, summary: "戦国時代の武将。" },
  { id: 2, name: "豊臣秀吉", image_url: null, summary: "天下統一を果たした武将。" },
];

describe("PersonaList", () => {
  test("ペルソナが0件の場合は案内文言のみを表示する", () => {
    render(<PersonaList personas={[]} />);

    expect(screen.getByText("ペルソナが登録されていません。")).toBeInTheDocument();
  });

  test("ペルソナ一覧をカードとして表示する", () => {
    render(<PersonaList personas={buildPersonas()} />);

    expect(screen.getByRole("link", { name: /織田信長/ })).toHaveAttribute("href", "/personas/1");
    expect(screen.getByRole("link", { name: /豊臣秀吉/ })).toHaveAttribute("href", "/personas/2");
  });

  test("検索欄に入力すると名前で絞り込まれる", async () => {
    const user = userEvent.setup();
    render(<PersonaList personas={buildPersonas()} />);

    await user.type(screen.getByLabelText("ペルソナ名で検索"), "信長");

    expect(screen.getByRole("link", { name: /織田信長/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /豊臣秀吉/ })).not.toBeInTheDocument();
  });

  test("検索結果が0件の場合は案内文言を表示する", async () => {
    const user = userEvent.setup();
    render(<PersonaList personas={buildPersonas()} />);

    await user.type(screen.getByLabelText("ペルソナ名で検索"), "存在しない人物");

    expect(screen.getByText("該当するペルソナが見つかりません")).toBeInTheDocument();
  });
});

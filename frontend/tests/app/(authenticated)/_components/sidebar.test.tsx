import { describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "@/app/(authenticated)/_components/sidebar";
import { logoutAction } from "@/app/(authenticated)/_actions";

vi.mock("@/app/(authenticated)/_actions", () => ({
  logoutAction: vi.fn(),
}));

const mockedLogoutAction = vi.mocked(logoutAction);

describe("Sidebar", () => {
  test("共通サイドバーの4項目を表示する（screen-list.md 3節）", () => {
    render(<Sidebar />);

    expect(screen.getByRole("link", { name: "新規チャット" })).toHaveAttribute(
      "href",
      "/chats/new",
    );
    expect(screen.getByRole("link", { name: "チャット履歴" })).toHaveAttribute("href", "/chats");
    expect(screen.getByRole("link", { name: "ペルソナ一覧" })).toHaveAttribute("href", "/personas");
    expect(screen.getByRole("button", { name: "ログアウト" })).toBeInTheDocument();
  });

  test("ログアウトボタン押下でlogoutActionを呼び出す", async () => {
    const user = userEvent.setup();
    render(<Sidebar />);

    await user.click(screen.getByRole("button", { name: "ログアウト" }));

    expect(mockedLogoutAction).toHaveBeenCalled();
  });
});

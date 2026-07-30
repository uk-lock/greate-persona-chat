import { describe, expect, test, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/app/login/_components/login-form";
import { loginAction } from "@/app/login/_actions";

vi.mock("@/app/login/_actions", () => ({
  loginAction: vi.fn(),
}));

const mockedLoginAction = vi.mocked(loginAction);

describe("LoginForm", () => {
  test("未入力で送信すると必須エラーを表示し、Server Actionを呼ばない", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(await screen.findByText("ログインIDを入力してください")).toBeInTheDocument();
    expect(screen.getByText("パスワードを入力してください")).toBeInTheDocument();
    expect(mockedLoginAction).not.toHaveBeenCalled();
  });

  test("入力内容でServer Actionを呼び出す", async () => {
    mockedLoginAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("ログインID"), "taro");
    await user.type(screen.getByLabelText("パスワード"), "secret123");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    await waitFor(() => {
      expect(mockedLoginAction).toHaveBeenCalledWith({
        login_id: "taro",
        password: "secret123",
      });
    });
  });

  test("認証失敗時はエラーメッセージを表示し、パスワード欄を空にする", async () => {
    mockedLoginAction.mockResolvedValueOnce({
      formError: "ログインIDまたはパスワードが正しくありません",
    });
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("ログインID"), "taro");
    await user.type(screen.getByLabelText("パスワード"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(
      await screen.findByText("ログインIDまたはパスワードが正しくありません"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("パスワード")).toHaveValue("");
  });
});

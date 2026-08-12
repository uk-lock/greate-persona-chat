import { describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SignupForm } from "@/app/signup/_components/signup-form";
import { signupAction } from "@/app/signup/_actions";

vi.mock("@/app/signup/_actions", () => ({
  signupAction: vi.fn(),
}));

const mockedSignupAction = vi.mocked(signupAction);

describe("SignupForm", () => {
  test("未入力で送信すると必須エラーを表示し、Server Actionを呼ばない", async () => {
    const user = userEvent.setup();
    render(<SignupForm />);

    await user.click(screen.getByRole("button", { name: "サインアップ" }));

    expect(await screen.findByText("ログインIDを入力してください")).toBeInTheDocument();
    expect(screen.getByText("パスワードを入力してください")).toBeInTheDocument();
    expect(screen.getByText("パスワード確認を入力してください")).toBeInTheDocument();
    expect(mockedSignupAction).not.toHaveBeenCalled();
  });

  test("パスワードとパスワード確認が不一致だとエラーを表示し、Server Actionを呼ばない", async () => {
    const user = userEvent.setup();
    render(<SignupForm />);

    await user.type(screen.getByLabelText("ログインID"), "taro");
    await user.type(screen.getByLabelText("パスワード"), "secret123");
    await user.type(screen.getByLabelText("パスワード確認"), "different");
    await user.click(screen.getByRole("button", { name: "サインアップ" }));

    expect(await screen.findByText("パスワードが一致しません")).toBeInTheDocument();
    expect(mockedSignupAction).not.toHaveBeenCalled();
  });

  test("入力内容でServer Actionを呼び出す", async () => {
    mockedSignupAction.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<SignupForm />);

    await user.type(screen.getByLabelText("ログインID"), "taro");
    await user.type(screen.getByLabelText("パスワード"), "secret123");
    await user.type(screen.getByLabelText("パスワード確認"), "secret123");
    await user.click(screen.getByRole("button", { name: "サインアップ" }));

    expect(mockedSignupAction).toHaveBeenCalledWith({
      login_id: "taro",
      password: "secret123",
      password_confirm: "secret123",
    });
  });

  test("登録失敗時はエラーメッセージを表示し、パスワード欄を空にする", async () => {
    mockedSignupAction.mockResolvedValueOnce({
      formError: "このログインIDは既に使用されています",
    });
    const user = userEvent.setup();
    render(<SignupForm />);

    await user.type(screen.getByLabelText("ログインID"), "taro");
    await user.type(screen.getByLabelText("パスワード"), "secret123");
    await user.type(screen.getByLabelText("パスワード確認"), "secret123");
    await user.click(screen.getByRole("button", { name: "サインアップ" }));

    expect(await screen.findByText("このログインIDは既に使用されています")).toBeInTheDocument();
    expect(screen.getByLabelText("パスワード")).toHaveValue("");
    expect(screen.getByLabelText("パスワード確認")).toHaveValue("");
  });
});

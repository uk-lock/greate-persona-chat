import { expect, test } from "@playwright/test";
import { TEST_PASSWORD, login, logout, signup, uniqueLoginId } from "./support/helpers";

/**
 * サインアップ／ログイン／ログアウト・認可周りのシナリオ（docs/testing.md 5節）。
 *
 * happy-path.spec.tsが「サインアップ→チャット」の一直線のhappy pathを検証するのに対し、
 * こちらはバリデーション・エラーメッセージ・認可（未ログイン時のリダイレクト）など
 * 分岐・異常系を中心に網羅する。LLM呼び出しを含まないため実行コストは低い。
 *
 * エラーメッセージの取得には`page.getByRole("alert")`ではなく`page.locator("form")
 * .getByRole("alert")`を使う。Next.jsはページ遷移をスクリーンリーダーへ通知するため、
 * 全ページに`role="alert"`を持つ非表示のdiv（`__next-route-announcer__`）を常駐させて
 * おり、スコープを絞らないとフォーム本来のエラーメッセージと衝突しうるため。
 */

test.describe("サインアップ", () => {
  test("必須項目が未入力のまま送信すると、送信されずバリデーションエラーが表示される", async ({
    page,
  }) => {
    await page.goto("/signup");
    await page.getByRole("button", { name: "サインアップ" }).click();

    await expect(page.getByText("ログインIDを入力してください")).toBeVisible();
    await expect(page.getByText("パスワードを入力してください")).toBeVisible();
    await expect(page.getByText("パスワード確認を入力してください")).toBeVisible();
    // クライアント側バリデーションのため画面遷移していないことも確認する
    await expect(page).toHaveURL(/\/signup$/);
  });

  test("ログインIDに半角英数字以外を入力するとバリデーションエラーが表示される", async ({
    page,
  }) => {
    await page.goto("/signup");
    await page.getByLabel("ログインID").fill("テスト太郎");
    await page.getByLabel("パスワード", { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel("パスワード確認").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "サインアップ" }).click();

    await expect(page.getByText("ログインIDは半角英数字で入力してください")).toBeVisible();
    await expect(page).toHaveURL(/\/signup$/);
  });

  test("パスワードとパスワード確認が一致しない場合、バリデーションエラーが表示される", async ({
    page,
  }) => {
    await page.goto("/signup");
    await page.getByLabel("ログインID").fill(uniqueLoginId("e2emismatch"));
    await page.getByLabel("パスワード", { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel("パスワード確認").fill(`${TEST_PASSWORD}x`);
    await page.getByRole("button", { name: "サインアップ" }).click();

    await expect(page.getByText("パスワードが一致しません")).toBeVisible();
    await expect(page).toHaveURL(/\/signup$/);
  });

  test("既に使われているログインIDでサインアップすると重複エラーが表示される", async ({ page }) => {
    const loginId = uniqueLoginId("e2edup");
    await signup(page, loginId);
    await logout(page);

    await page.goto("/signup");
    await page.getByLabel("ログインID").fill(loginId);
    await page.getByLabel("パスワード", { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel("パスワード確認").fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "サインアップ" }).click();

    await expect(page.locator("form").getByRole("alert")).toHaveText(
      "このログインIDは既に使用されています",
    );
    // パスワード欄がリセットされ、ログインIDは残っていること（signup-form.tsx参照）
    await expect(page.getByLabel("パスワード", { exact: true })).toHaveValue("");
    await expect(page.getByLabel("ログインID")).toHaveValue(loginId);
  });

  test("ログイン済みの状態で/signupへアクセスすると/chatsへリダイレクトされる", async ({
    page,
  }) => {
    await signup(page, uniqueLoginId("e2esignupredir"));
    await page.goto("/signup");
    await expect(page).toHaveURL(/\/chats$/);
  });
});

test.describe("ログイン", () => {
  test("誤ったパスワードでログインするとエラーが表示されパスワード欄がクリアされる", async ({
    page,
  }) => {
    const loginId = uniqueLoginId("e2ewrongpw");
    await signup(page, loginId);
    await logout(page);

    await page.goto("/login");
    await page.getByLabel("ログインID").fill(loginId);
    await page.getByLabel("パスワード", { exact: true }).fill("wrongPassword123");
    await page.getByRole("button", { name: "ログイン" }).click();

    await expect(page.locator("form").getByRole("alert")).toHaveText(
      "ログインIDまたはパスワードが正しくありません",
    );
    await expect(page.getByLabel("パスワード", { exact: true })).toHaveValue("");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("存在しないログインIDでログインしても、パスワード誤りと同じエラーメッセージが表示される", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("ログインID").fill(uniqueLoginId("e2enouser"));
    await page.getByLabel("パスワード", { exact: true }).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "ログイン" }).click();

    // ログインID・パスワードいずれの誤りかを区別させない（ユーザー列挙対策）
    await expect(page.locator("form").getByRole("alert")).toHaveText(
      "ログインIDまたはパスワードが正しくありません",
    );
  });

  test("ログイン済みの状態で/loginへアクセスすると/chatsへリダイレクトされる", async ({ page }) => {
    const loginId = uniqueLoginId("e2eloginredir");
    await signup(page, loginId);
    await page.goto("/login");
    await expect(page).toHaveURL(/\/chats$/);
  });

  test("連続ログイン失敗を繰り返すとアカウントがロックされ、正しいパスワードでも拒否される", async ({
    page,
  }) => {
    // LOGIN_FAILURE_LIMIT（backend/app/config/constants.py、既定10）回の失敗を要するため長め
    test.slow();

    const loginId = uniqueLoginId("e2elockout");
    await signup(page, loginId);
    await logout(page);

    await page.goto("/login");
    for (let attempt = 0; attempt < 10; attempt += 1) {
      await page.getByLabel("ログインID").fill(loginId);
      await page.getByLabel("パスワード", { exact: true }).fill("wrongPassword123");
      await page.getByRole("button", { name: "ログイン" }).click();
      await expect(page.locator("form").getByRole("alert")).toBeVisible();
    }

    // 10回目の失敗でロックされているため、正しいパスワードでもUserLockedError（423）になる
    await page.getByLabel("ログインID").fill(loginId);
    await page.getByLabel("パスワード", { exact: true }).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page.locator("form").getByRole("alert")).toHaveText(
      "連続ログイン失敗によりロックされています",
    );
  });
});

test.describe("認可・ログアウト", () => {
  for (const path of ["/chats", "/chats/new", "/personas"]) {
    test(`未ログイン状態で${path}にアクセスすると/loginへリダイレクトされる`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login$/);
    });
  }

  test("存在しないchat_id・persona_idへの直接アクセスは一覧画面へリダイレクトされる", async ({
    page,
  }) => {
    await signup(page, uniqueLoginId("e2enotfound"));

    await page.goto("/chats/00000000-0000-0000-0000-000000000000");
    await expect(page).toHaveURL(/\/chats$/);

    await page.goto("/personas/999999999");
    await expect(page).toHaveURL(/\/personas$/);
  });

  test("ログアウトすると/loginへ遷移し、以後保護ページにアクセスできなくなる", async ({ page }) => {
    await signup(page, uniqueLoginId("e2elogout"));
    await logout(page);

    await page.goto("/chats");
    await expect(page).toHaveURL(/\/login$/);
  });
});

test("サインアップ・ログアウト・再ログインまでの一連の操作ができる", async ({ page }) => {
  const loginId = uniqueLoginId("e2erelogin");
  await signup(page, loginId);
  await logout(page);
  await login(page, loginId);
  await expect(page.getByRole("heading", { name: "チャット履歴" })).toBeVisible();
});

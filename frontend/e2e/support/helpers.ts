import { expect, type Page } from "@playwright/test";

/**
 * 全E2Eシナリオ共通のヘルパー（サインアップ・ログイン・ログアウト）。
 *
 * `fullyParallel: true`（playwright.config.ts）のため、同一DB上で複数テストが並行実行される。
 * ログインIDの衝突を避けるため、テスト側は必ず{@link uniqueLoginId}で生成した値を使うこと
 * （固定値・Date.now()のみだと並列実行時に衝突しうる）。
 */
export const TEST_PASSWORD = "e2eTestPassword123";

/** 並列実行しても衝突しない半角英数字のログインIDを生成する（db.md m_user.login_id仕様）。 */
export const uniqueLoginId = (prefix: string): string => {
  const random = Math.random().toString(36).slice(2, 8);
  return `${prefix}${Date.now()}${random}`;
};

/** サインアップ画面から新規登録する。成功時は自動ログインの上 /chats へ遷移する。 */
export const signup = async (
  page: Page,
  loginId: string,
  password: string = TEST_PASSWORD,
): Promise<void> => {
  await page.goto("/signup");
  await page.getByLabel("ログインID").fill(loginId);
  await page.getByLabel("パスワード", { exact: true }).fill(password);
  await page.getByLabel("パスワード確認").fill(password);
  await page.getByRole("button", { name: "サインアップ" }).click();
  await expect(page).toHaveURL(/\/chats$/);
};

/** ログイン画面からログインする。成功時は /chats へ遷移する。 */
export const login = async (
  page: Page,
  loginId: string,
  password: string = TEST_PASSWORD,
): Promise<void> => {
  await page.goto("/login");
  await page.getByLabel("ログインID").fill(loginId);
  await page.getByLabel("パスワード", { exact: true }).fill(password);
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(/\/chats$/);
};

/** サイドバーからログアウトする。成功時は /login へ遷移する。 */
export const logout = async (page: Page): Promise<void> => {
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page).toHaveURL(/\/login$/);
};

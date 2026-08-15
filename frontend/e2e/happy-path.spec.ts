import { expect, test } from "@playwright/test";

/**
 * サインアップ → ペルソナ一覧 → チャット開始 → メッセージ送信 → 応答受信までの
 * happy pathを通しで検証する最初のE2Eシナリオ（docs/testing.md 5節）。
 *
 * 実行前提: `backend/tools/reset_e2e_data`によって初期ペルソナが最低1件投入済みであること。
 * ペルソナ名自体は各自の`backend/data/init_persona.json`に依存するため、
 * 特定の名前をハードコードせず一覧の先頭要素を使う。
 */
test("サインアップからペルソナとのチャット送信までの一連の操作ができる", async ({ page }) => {
  // サインアップ〜LLM応答受信まで複数ステップを直列で繋げるため、既定のタイムアウトでは
  // 環境負荷が高いときに不足することがある（docs/testing.md 5節）。
  test.slow();

  const loginId = `e2euser${Date.now()}`;
  const password = "e2eTestPassword123";

  await page.goto("/signup");
  await page.getByLabel("ログインID").fill(loginId);
  await page.getByLabel("パスワード", { exact: true }).fill(password);
  await page.getByLabel("パスワード確認").fill(password);
  await page.getByRole("button", { name: "サインアップ" }).click();

  // サインアップ成功時は自動ログインの上 /chats へ遷移する
  await expect(page).toHaveURL(/\/chats$/);

  await page.goto("/personas");
  const firstPersonaLink = page.locator('a[href^="/personas/"]').first();
  await expect(firstPersonaLink).toBeVisible();
  await firstPersonaLink.click();

  await page.getByRole("link", { name: "チャットを始める" }).click();
  await expect(page).toHaveURL(/\/chats\/new/);

  // persona_idクエリパラメータで1体のみ事前選択済み・デフォルトモードは
  // 「あなたも参加する」（お題入力不要）のため、そのまま作成できる
  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  await page.getByPlaceholder("メッセージを入力").fill("こんにちは");
  await page.getByRole("button", { name: "送信" }).click();

  // 自分のメッセージ＋ペルソナからの応答の2件がバブルとして表示されるまで待つ
  // （LLM応答待ちのため長めのタイムアウト。E2E_REPLY_MODEL等で安価なモデルに切り替える運用）
  await expect(page.locator("p.whitespace-pre-wrap")).toHaveCount(2, { timeout: 45_000 });
});

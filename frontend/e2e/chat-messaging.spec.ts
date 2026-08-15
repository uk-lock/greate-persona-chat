import { expect, test } from "@playwright/test";
import { signup, uniqueLoginId } from "./support/helpers";

/**
 * チャット画面（S03）でのメッセージ送受信のシナリオ（docs/testing.md 5節）。
 *
 * 「メッセージ送信」「ペルソナ同士の会話開始」は実際にLLM APIを呼び出す
 * （`E2E_REPLY_MODEL`等で安価なモデルに切り替える運用。5.3節）ため、このファイルに
 * LLM呼び出しを伴うシナリオを集約し、他のファイル（chat-creation.spec.ts等）では
 * 作成・一覧・削除などLLM呼び出しを伴わない操作のみを検証する。
 */

const MESSAGE_MAX_LENGTH = 500;

test.beforeEach(async ({ page }) => {
  await signup(page, uniqueLoginId("e2emsg"));
});

test("メッセージ入力欄は上限文字数を超えて入力できず、未入力では送信ボタンが無効になる", async ({
  page,
}) => {
  await page.goto("/chats/new");
  await page.locator("ul.grid > li button").first().click();
  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  const textarea = page.getByPlaceholder("メッセージを入力");
  await expect(page.getByRole("button", { name: "送信" })).toBeDisabled();

  // maxlength属性は`.fill()`（スクリプトによるvalue代入）では効かないため、実際の
  // キー入力（pressSequentially）で上限を超えて打鍵し、ブラウザ側の制約を検証する
  await textarea.pressSequentially("あ".repeat(MESSAGE_MAX_LENGTH + 5));
  await expect(textarea).toHaveValue("あ".repeat(MESSAGE_MAX_LENGTH));
  await expect(page.getByRole("button", { name: "送信" })).toBeEnabled();

  // 空白のみの入力は送信不可（handleSend: trimmed判定）
  await textarea.fill("   ");
  await expect(page.getByRole("button", { name: "送信" })).toBeDisabled();
});

test("メッセージを送信すると自分の発言が即座に表示され、ペルソナから応答が届く", async ({
  page,
}) => {
  test.slow();

  await page.goto("/chats/new");
  await page.locator("ul.grid > li button").first().click();
  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  await page.getByPlaceholder("メッセージを入力").fill("こんにちは");
  await page.getByRole("button", { name: "送信" }).click();

  // 送信直後：入力欄がクリアされ、自分の発言が先に表示される
  await expect(page.getByPlaceholder("メッセージを入力")).toHaveValue("");
  await expect(page.locator("p.whitespace-pre-wrap").first()).toHaveText("こんにちは");

  // ペルソナからの応答（LLM呼び出し）が届くまで待つ。生成中は送信欄が無効化される
  await expect(page.getByPlaceholder("メッセージを入力")).toBeDisabled();
  await expect(page.locator("p.whitespace-pre-wrap")).toHaveCount(2, { timeout: 45_000 });
  await expect(page.getByPlaceholder("メッセージを入力")).toBeEnabled();
});

test("PERSONA_ONLYモードで「開始」を押すとペルソナ同士の会話が進行する", async ({ page }) => {
  test.slow();

  await page.goto("/chats/new");
  const cards = page.locator("ul.grid > li button");
  const count = await cards.count();
  test.skip(count < 2, "ペルソナ同士の会話にはペルソナが2体以上必要");

  await cards.nth(0).click();
  await cards.nth(1).click();
  await page.getByRole("radio", { name: "ペルソナ同士の会話を観る" }).check();
  await page.getByPlaceholder("例：理想のリーダーシップとは").fill("理想の指導者とは");
  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  await page.getByRole("button", { name: "開始" }).click();
  await expect(page.getByRole("button", { name: "開始" })).toBeDisabled();
  await expect(page.locator("p.whitespace-pre-wrap").first()).toBeVisible({ timeout: 45_000 });
});

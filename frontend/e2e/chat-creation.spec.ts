import { expect, test } from "@playwright/test";
import { signup, uniqueLoginId } from "./support/helpers";

/**
 * 新規チャット画面（S01）でのペルソナ選択・チャットモード切り替えと、チャット履歴画面（S02）
 * での一覧表示・削除のシナリオ（docs/testing.md 5節）。
 *
 * チャット作成自体（`POST /chats`）はLLM呼び出しを伴わない（メッセージ送信・「開始」操作で
 * 初めてLLMが呼ばれる）ため、このファイルのシナリオは実行コストが低い。メッセージ送受信を
 * 伴うシナリオはchat-messaging.spec.tsに分離してある。
 */

const CHAT_PERSONA_MAX_COUNT = 5;

test.beforeEach(async ({ page }) => {
  await signup(page, uniqueLoginId("e2echatnew"));
});

test("ペルソナ未選択では「チャット開始」ボタンが無効になっている", async ({ page }) => {
  await page.goto("/chats/new");
  await expect(page.getByRole("button", { name: "チャット開始" })).toBeDisabled();
});

test("ペルソナを選択すると選択中リストに反映され、×で選択解除できる", async ({ page }) => {
  await page.goto("/chats/new");
  const firstCard = page.locator("ul.grid > li button").first();
  const firstName = await firstCard.locator("p").innerText();
  await firstCard.click();

  await expect(page.getByText(/選択中のペルソナ（1\/5体選択中）/)).toBeVisible();
  await expect(page.getByRole("button", { name: "チャット開始" })).toBeEnabled();

  await page.getByRole("button", { name: `${firstName}の選択を解除` }).click();
  await expect(
    page.getByText(`ペルソナを${1}体以上選択してください。`, { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "チャット開始" })).toBeDisabled();
});

test(`ペルソナは最大${CHAT_PERSONA_MAX_COUNT}体までしか選択できない`, async ({ page }) => {
  await page.goto("/chats/new");
  const cards = page.locator("ul.grid > li button");
  const count = await cards.count();
  test.skip(
    count <= CHAT_PERSONA_MAX_COUNT,
    "上限超過を検証するにはペルソナがCHAT_PERSONA_MAX_COUNT+1体以上必要",
  );

  for (let i = 0; i < CHAT_PERSONA_MAX_COUNT; i += 1) {
    await cards.nth(i).click();
  }
  await expect(page.getByText(/選択中のペルソナ（5\/5体選択中）/)).toBeVisible();

  // 上限に達した未選択カードは無効化され、選択数が増えないことを確認する
  const extraCard = cards.nth(CHAT_PERSONA_MAX_COUNT);
  await expect(extraCard).toBeDisabled();
  await expect(page.getByText(/選択中のペルソナ（5\/5体選択中）/)).toBeVisible();
});

test("「ペルソナ同士の会話を観る」モードではお題未入力だと開始ボタンが無効で、入力すると有効になる", async ({
  page,
}) => {
  await page.goto("/chats/new");
  await page.locator("ul.grid > li button").first().click();
  await page.getByRole("radio", { name: "ペルソナ同士の会話を観る" }).check();

  await expect(page.getByRole("button", { name: "チャット開始" })).toBeDisabled();
  await page.getByPlaceholder("例：理想のリーダーシップとは").fill("理想の指導者とは");
  await expect(page.getByRole("button", { name: "チャット開始" })).toBeEnabled();
});

test("USER_PARTICIPATEDでチャットを作成すると、チャット画面に遷移し参加者が表示される", async ({
  page,
}) => {
  await page.goto("/chats/new");
  const firstCard = page.locator("ul.grid > li button").first();
  const firstName = await firstCard.locator("p").innerText();
  await firstCard.click();

  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  await expect(page.getByRole("heading", { name: "新規チャット" })).toBeVisible();
  await expect(page.getByText("あなた")).toBeVisible();
  await expect(page.getByTitle(firstName)).toBeVisible();
  await expect(page.getByText("メッセージを送ってみましょう")).toBeVisible();
});

test("PERSONA_ONLYでチャットを作成すると、お題がヘッダーに表示され「開始」操作で送信できる状態になる", async ({
  page,
}) => {
  await page.goto("/chats/new");
  await page.locator("ul.grid > li button").first().click();
  await page.getByRole("radio", { name: "ペルソナ同士の会話を観る" }).check();
  await page.getByPlaceholder("例：理想のリーダーシップとは").fill("理想の指導者とは");
  await page.getByRole("button", { name: "チャット開始" }).click();

  await expect(page).toHaveURL(/\/chats\/[^/]+$/);
  await expect(page.getByText("お題：理想の指導者とは")).toBeVisible();
  await expect(page.getByText("開始ボタンを押して会話を始めましょう")).toBeVisible();
  await expect(page.getByRole("button", { name: "開始" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "停止" })).toBeDisabled();
});

test("チャット履歴が空の場合、案内文が表示される", async ({ page }) => {
  await page.goto("/chats");
  await expect(
    page.getByText("まだチャットがありません。新規チャットから会話を始めましょう。"),
  ).toBeVisible();
});

test("作成したチャットがチャット履歴一覧に表示され、削除できる", async ({ page }) => {
  await page.goto("/chats/new");
  await page.locator("ul.grid > li button").first().click();
  await page.getByRole("button", { name: "チャット開始" }).click();
  await expect(page).toHaveURL(/\/chats\/[^/]+$/);

  // チャット作成から一覧への反映までごく短い遅延がある（Neon側の接続経路によるものと
  // 見られる。docs/testing.md 5節）ため、固定sleepではなく再ナビゲーションを伴う
  // リトライで待つ。
  const row = page.locator("li", { hasText: "新規チャット" }).first();
  await expect(async () => {
    await page.goto("/chats");
    await expect(row).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 15_000 });

  // キャンセルでは削除されない
  await row.getByRole("button", { name: /を削除$/ }).click();
  await expect(page.getByText("このチャットを削除しますか？")).toBeVisible();
  await page.getByRole("button", { name: "キャンセル" }).click();
  await expect(page.getByText("このチャットを削除しますか？")).toBeHidden();
  await expect(row).toBeVisible();

  // OKで削除される
  await row.getByRole("button", { name: /を削除$/ }).click();
  await page.getByRole("button", { name: "OK" }).click();
  await expect(
    page.getByText("まだチャットがありません。新規チャットから会話を始めましょう。"),
  ).toBeVisible();
});

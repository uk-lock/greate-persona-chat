import { expect, test } from "@playwright/test";
import { signup, uniqueLoginId } from "./support/helpers";

/**
 * ペルソナ一覧（S04）・ペルソナ詳細（S05）のシナリオ（docs/testing.md 5節）。
 *
 * ペルソナ名自体は各自の`backend/data/init_persona.json`に依存するため、特定の名前を
 * ハードコードせず一覧の要素・件数から動的に検証する（happy-path.spec.tsと同じ方針）。
 * LLM呼び出しを含まないため実行コストは低い。
 */

test.beforeEach(async ({ page }) => {
  await signup(page, uniqueLoginId("e2epersona"));
});

test("ペルソナ一覧に登録済みのペルソナが表示される", async ({ page }) => {
  await page.goto("/personas");
  await expect(page.getByRole("heading", { name: "ペルソナ一覧" })).toBeVisible();
  await expect(page.locator('a[href^="/personas/"]').first()).toBeVisible();
});

test("ペルソナ名で検索すると一覧が絞り込まれる", async ({ page }) => {
  await page.goto("/personas");
  const firstCard = page.locator('a[href^="/personas/"]').first();
  await expect(firstCard).toBeVisible();
  const firstName = await firstCard.locator("p.font-display").innerText();

  await page.getByPlaceholder("例：織田信長").fill(firstName);

  const results = page.locator('a[href^="/personas/"]');
  await expect(results).toHaveCount(1);
  await expect(results.first()).toContainText(firstName);
});

test("該当しない検索語では「該当するペルソナが見つかりません」と表示される", async ({ page }) => {
  await page.goto("/personas");
  await page.getByPlaceholder("例：織田信長").fill("該当しないはずの検索語xyz123");
  await expect(page.getByText("該当するペルソナが見つかりません")).toBeVisible();
  await expect(page.locator('a[href^="/personas/"]')).toHaveCount(0);
});

test("ペルソナをクリックすると詳細画面へ遷移し、一覧に戻ることもできる", async ({ page }) => {
  await page.goto("/personas");
  const firstCard = page.locator('a[href^="/personas/"]').first();
  const href = await firstCard.getAttribute("href");
  const firstName = await firstCard.locator("p.font-display").innerText();
  await firstCard.click();

  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expect(page.getByRole("heading", { name: firstName, level: 1 })).toBeVisible();

  await page.getByRole("link", { name: "一覧に戻る" }).click();
  await expect(page).toHaveURL(/\/personas$/);
});

test("詳細画面から「チャットを始める」を押すと、対象ペルソナが事前選択された新規チャット画面へ遷移する", async ({
  page,
}) => {
  await page.goto("/personas");
  const firstCard = page.locator('a[href^="/personas/"]').first();
  const firstName = await firstCard.locator("p.font-display").innerText();
  await firstCard.click();

  await page.getByRole("link", { name: "チャットを始める" }).click();
  await expect(page).toHaveURL(/\/chats\/new/);

  // persona_idクエリパラメータにより、遷移元のペルソナが選択中リストに含まれている
  await expect(page.getByText(/選択中のペルソナ（1\/5体選択中）/)).toBeVisible();
  await expect(page.getByRole("button", { name: `${firstName}の選択を解除` })).toBeVisible();
});

test("存在しないpersona_idへアクセスするとペルソナ一覧へリダイレクトされる", async ({ page }) => {
  await page.goto("/personas/999999999");
  await expect(page).toHaveURL(/\/personas$/);
});

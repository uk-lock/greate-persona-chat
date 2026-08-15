import { defineConfig, devices } from "@playwright/test";

/**
 * E2E（Playwright）設定。
 *
 * backend/frontendはあらかじめDockerfile.prod相当でビルド・起動済みであることを前提とし、
 * このファイルは`webServer`を持たない（起動は`compose.e2e.yml`側の責務）。
 * `E2E_BASE_URL`は`compose.e2e.yml`のe2eサービスから`http://127.0.0.1:3000`が渡される想定
 * （docs/testing.md 5節。frontendとnetwork_modeを共有し、Secure Cookie維持のため
 * loopbackアドレスでアクセスする）。
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  // Neonのコールドスタート・並列実行時の負荷により、単純な画面遷移でも既定の
  // タイムアウトに収まらないことがあったため、余裕を持たせている（docs/testing.md 5節）。
  // 60秒・10秒でもまだ不足するケースが見つかったため、さらに緩めている。
  timeout: 90_000,
  expect: {
    timeout: 15_000,
  },
  // 並列実行しすぎると同一backend/DBへの負荷が上がりレイテンシが悪化するため、
  // ある程度絞る（CPUコア数依存の既定値だと環境によって不安定になりやすい）。
  // 4でもまだ負荷が高い事象が見られたため、さらに絞っている。
  workers: 2,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    // retriesが既定0（非CI）のため"on-first-retry"だとtraceが一切残らない。
    // 失敗したテストのtrace/screenshotは常に残す。
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

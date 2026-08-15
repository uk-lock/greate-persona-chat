import { configDefaults, defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // frontend/e2e/配下はPlaywright専用のテストファイル（*.spec.ts）のため、
    // vitestのデフォルトの対象パターンから除外する（docs/testing.md 5節）。
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});

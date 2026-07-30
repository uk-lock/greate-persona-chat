import { describe, expect, test } from "vitest";
import { formatUpdatedAt } from "@/app/(authenticated)/chats/_format";

describe("formatUpdatedAt", () => {
  test("ISO日時文字列を日本語の日時表記に整形する", () => {
    expect(formatUpdatedAt("2026-07-30T09:05:00+09:00")).toBe("2026/07/30 09:05");
  });
});

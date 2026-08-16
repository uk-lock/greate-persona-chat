import { describe, expect, test } from "vitest";
import { truncateSummary } from "@/app/(authenticated)/personas/_format";

describe("truncateSummary", () => {
  test("50文字以内の場合はそのまま返す", () => {
    expect(truncateSummary("戦国時代の武将。")).toBe("戦国時代の武将。");
  });

  test("50文字を超える場合は50文字で切り詰めて末尾に…を付ける", () => {
    const summary = "あ".repeat(60);
    const result = truncateSummary(summary);
    expect(result).toBe(`${"あ".repeat(50)}…`);
  });

  test("nullの場合は空文字を返す", () => {
    expect(truncateSummary(null)).toBe("");
  });
});

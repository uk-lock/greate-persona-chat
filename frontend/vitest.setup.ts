import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdomはscrollIntoViewを実装していないため、テスト実行時のみno-opを補う。
Element.prototype.scrollIntoView = vi.fn();

afterEach(() => {
  cleanup();
});

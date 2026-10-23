import { describe, expect, it } from "vitest";

import {
  cn,
  formatDate,
  formatNumber,
  formatPercent,
  humanizeAction,
  initials,
  pluralize,
  shortHash,
  titleCase,
  truncate,
} from "./utils";

describe("ui formatting helpers", () => {
  it("merges conflicting tailwind classes", () => {
    expect(cn("px-2 text-sm", "px-4", false && "hidden")).toBe("text-sm px-4");
  });

  it("formats ISO dates and falls back safely", () => {
    expect(formatDate("2026-10-23T10:00:00Z", "dd MMM yyyy")).toBe("23 Oct 2026");
    expect(formatDate(null)).toBe("—");
    expect(formatDate("not-a-date")).toBe("—");
  });

  it("humanizes snake, kebab, and action identifiers", () => {
    expect(titleCase("forced_labour-risk")).toBe("Forced Labour Risk");
    expect(titleCase(null)).toBe("");
    expect(humanizeAction("approval.requested")).toBe("Approval · Requested");
  });

  it("derives initials safely", () => {
    expect(initials("Rafiq Hasan")).toBe("RH");
    expect(initials("Ayesha")).toBe("A");
    expect(initials("")).toBe("?");
  });

  it("truncates long values without dropping short values", () => {
    expect(truncate("short", 10)).toBe("short");
    expect(truncate("abcdefghij", 6)).toBe("abcde…");
  });

  it("formats counts and percentages", () => {
    expect(formatNumber(1234)).toBe("1,234");
    expect(formatNumber(null)).toBe("—");
    expect(formatPercent(62.5, 1)).toBe("62.5%");
    expect(formatPercent(62.5, 0)).toBe("63%");
    expect(formatPercent(null)).toBe("—");
  });

  it("shortens hashes and handles empty values", () => {
    expect(shortHash("abcdef0123456789", 8)).toBe("abcdef01…");
    expect(shortHash("abc", 8)).toBe("abc");
    expect(shortHash(null)).toBe("—");
  });

  it("pluralizes labels", () => {
    expect(pluralize(1, "risk")).toBe("1 risk");
    expect(pluralize(3, "risk")).toBe("3 risks");
    expect(pluralize(2, "source", "sources")).toBe("2 sources");
  });
});

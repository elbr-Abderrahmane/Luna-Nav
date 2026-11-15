import { describe, expect, it } from "vitest";
import { formatDuration, formatValue } from "./format";

describe("format", () => {
  it("formatDuration matches the API text style", () => {
    expect(formatDuration(76.2)).toBe("3 d 4 h 12 min");
    expect(formatDuration(21 + 37 / 60)).toBe("21 h 37 min");
    expect(formatDuration(0.5)).toBe("30 min");
    expect(formatDuration(48)).toBe("2 d 0 h 0 min");
  });
  it("missing values are never turned into numbers", () => {
    expect(formatDuration(null)).toBe("Not available");
    expect(formatDuration(-1)).toBe("Not available");
    expect(formatValue(undefined, "deg")).toBe("Not available");
    expect(formatValue(NaN)).toBe("Not available");
    expect(formatValue(12.345, "deg", 1)).toBe("12.3 deg");
  });
});

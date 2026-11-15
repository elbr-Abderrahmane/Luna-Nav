import { describe, expect, it } from "vitest";
import type { TimeWindow } from "../api/types";
import { barSegments } from "./windows";

const win = (starts_in_h: number, duration_h: number, open_start = false, open_end = false): TimeWindow => ({
  start_utc: "", end_utc: "", duration_h, duration_text: `${duration_h} h`, starts_in_h,
  open_at_window_start: open_start, open_at_window_end: open_end,
});

describe("barSegments", () => {
  it("places a window as fractions of the lunar day", () => {
    const [s] = barSegments([win(100, 50)], 700);
    expect(s.left).toBeCloseTo(100 / 700);
    expect(s.width).toBeCloseTo(50 / 700);
  });
  it("clips windows that run past the end and keeps the open flag", () => {
    const [s] = barSegments([win(650, 100, false, true)], 700);
    expect(s.left + s.width).toBeCloseTo(1);
    expect(s.open_end).toBe(true);
  });
  it("skips empty windows", () => {
    expect(barSegments([win(700, 10), win(10, 0)], 700)).toHaveLength(0);
  });
});

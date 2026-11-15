import type { TimeWindow } from "../api/types";
import { WINDOW_HOURS } from "./constants";

export interface BarSegment {
  /** 0..1 position of the left edge along the bar */
  left: number;
  /** 0..1 width */
  width: number;
  /** the window continues past the analysis window start / end (draw an open edge) */
  open_start: boolean;
  open_end: boolean;
  duration_text: string;
}

/**
 * Windows -> segments for the sunlit / Earth / both bars.
 * `starts_in_h` and `duration_h` are measured from the landing date (README 6.4).
 * Pass the scenario's own window length if it is not one lunar day.
 */
export function barSegments(windows: TimeWindow[], windowHours: number = WINDOW_HOURS): BarSegment[] {
  const out: BarSegment[] = [];
  for (const w of windows) {
    const start = Math.max(0, w.starts_in_h);
    const end = Math.min(windowHours, w.starts_in_h + w.duration_h);
    if (end <= start) continue;
    out.push({
      left: start / windowHours,
      width: (end - start) / windowHours,
      open_start: w.open_at_window_start,
      open_end: w.open_at_window_end,
      duration_text: w.duration_text,
    });
  }
  return out;
}

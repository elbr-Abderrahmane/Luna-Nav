import type { Countdown, NextEvent } from "../api/types";
import { formatDuration } from "./format";

export type Body = "sun" | "earth";
const EVENTS: Record<Body, string[]> = { sun: ["sunset", "sunrise"], earth: ["earthset", "earthrise"] };

export interface LiveCountdown {
  event: string;
  remaining_h: number;
  text: string;
}

/**
 * Countdown after dragging the slider (README 6.3): the API's `next_events` are measured from the
 * landing moment, so remaining = in_h - sliderHours. Returns null when no later event is listed:
 * then show `countdown.summary` from the API instead of a guess. Check with P3 whether
 * `next_events` lists every event of the window or only the next few.
 */
export function liveCountdown(body: Body, nextEvents: NextEvent[], sliderHours: number): LiveCountdown | null {
  const next = nextEvents
    .filter((e) => EVENTS[body].includes(e.event) && e.in_h > sliderHours)
    .sort((a, b) => a.in_h - b.in_h)[0];
  if (!next) return null;
  const remaining_h = next.in_h - sliderHours;
  return { event: next.event, remaining_h, text: formatDuration(remaining_h) };
}

/** At slider 0 the API's own pre-formatted text is shown, not our formatting. */
export function countdownLabel(body: Body, countdown: Countdown, nextEvents: NextEvent[], sliderHours: number): string {
  if (sliderHours <= 0 || countdown.beyond_window) return countdown.summary;
  const live = liveCountdown(body, nextEvents, sliderHours);
  if (!live) return countdown.summary;
  const name = live.event.charAt(0).toUpperCase() + live.event.slice(1);
  return `${name} in ${live.text}`;
}

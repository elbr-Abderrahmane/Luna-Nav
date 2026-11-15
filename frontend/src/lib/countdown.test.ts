import { describe, expect, it } from "vitest";
import type { Countdown, NextEvent } from "../api/types";
import { countdownLabel, liveCountdown } from "./countdown";

const ev = (event: string, in_h: number): NextEvent => ({ event, t_utc: "", in_h, in_text: "" });
const events = [ev("earthset", 10), ev("sunset", 30), ev("earthrise", 40)];

describe("liveCountdown", () => {
  it("counts down to the next Earth event after the slider", () => {
    expect(liveCountdown("earth", events, 0)?.event).toBe("earthset");
    const l = liveCountdown("earth", events, 12);
    expect(l?.event).toBe("earthrise");
    expect(l?.remaining_h).toBeCloseTo(28);
  });
  it("filters by body", () => {
    expect(liveCountdown("sun", events, 0)?.event).toBe("sunset");
  });
  it("returns null when nothing later is listed", () => {
    expect(liveCountdown("earth", events, 50)).toBeNull();
  });
  it("countdownLabel shows the API summary at slider 0 and when beyond the window", () => {
    const c = { summary: "Earthset in 10 h", beyond_window: false } as Countdown;
    expect(countdownLabel("earth", c, events, 0)).toBe("Earthset in 10 h");
    expect(countdownLabel("earth", c, events, 12)).toBe("Earthrise in 1 d 4 h 0 min");
    expect(countdownLabel("sun", { summary: "Sun stays up", beyond_window: true } as Countdown, events, 12)).toBe("Sun stays up");
  });
});

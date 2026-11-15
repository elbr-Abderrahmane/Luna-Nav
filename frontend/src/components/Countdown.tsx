import type { Countdown as CountdownData, NextEvent } from "../api/types";
import { countdownLabel, liveCountdown, type Body } from "../lib/countdown";

interface Props {
  body: Body;
  countdown: CountdownData;
  nextEvents: NextEvent[];
  sliderHours: number;
  /** is the centre of the disk above the horizon right now (for the state line) */
  up?: boolean;
}

/** "Earthrise in 21 h 37 min": the API's own text at the landing moment, derived from next_events once the slider moves. */
export function Countdown({ body, countdown, nextEvents, sliderHours, up }: Props) {
  // After the slider moves, never show the landing-moment text as if it were current.
  const stale = sliderHours > 0 && !countdown.beyond_window && liveCountdown(body, nextEvents, sliderHours) === null;
  const text = stale ? "No later change in the event list" : countdownLabel(body, countdown, nextEvents, sliderHours);
  const m = text.match(/^(\w+) in (.+)$/);
  return (
    <div className={`tile tile-${body}`}>
      <div className="tile-head">
        <span className="dot" />
        {body === "sun" ? "Sun" : "Earth"}
      </div>
      {m ? (
        <>
          <div className="tile-event">{m[1]} in</div>
          <div className="tile-time">{m[2]}</div>
        </>
      ) : (
        <div className="tile-time long">{text}</div>
      )}
      {up !== undefined && <div className={`state ${up ? "up" : "down"}`}>{up ? "Above the horizon" : "Below the horizon"}</div>}
    </div>
  );
}

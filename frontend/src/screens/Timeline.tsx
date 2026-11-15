import { useEffect, useState } from "react";
import type { Screen } from "../components/AppShell";
import { Countdown } from "../components/Countdown";
import { ErrorState } from "../components/ErrorState";
import { HorizonView } from "../components/HorizonView";
import { Loading } from "../components/Loading";
import { PowerReadout } from "../components/PowerReadout";
import { WarningList } from "../components/WarningList";
import { WindowBars } from "../components/WindowBars";
import { WINDOW_HOURS } from "../lib/constants";
import { formatUtc } from "../lib/utc";
import { useScenarioStore } from "../state/scenarioStore";
import { skyView, useActive } from "../state/useActive";

const STEP_H = 6; // hours per tick while playing
const TICK_MS = 90; // a full lunar day plays in about 11 seconds

export function Timeline({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const { card, conditions, timeline } = useActive();
  const sliderHours = useScenarioStore((s) => s.sliderHours);
  const setSlider = useScenarioStore((s) => s.setSliderHours);
  const [playing, setPlaying] = useState(false);

  const data = timeline.data ?? conditions.data;
  const max = Math.round(data?.window.duration_h ?? WINDOW_HOURS);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      const next = useScenarioStore.getState().sliderHours + STEP_H;
      if (next >= max) {
        setSlider(max);
        setPlaying(false);
      } else setSlider(next);
    }, TICK_MS);
    return () => window.clearInterval(id);
  }, [playing, max, setSlider]);

  if (!card) {
    return (
      <section className="panel empty">
        <h1>No scenario selected</h1>
        <p className="muted">Add a scenario first, then open its timeline.</p>
        <button className="btn primary" onClick={() => onNavigate("builder")}>
          Go to Scenarios
        </button>
      </section>
    );
  }
  if (timeline.isError) {
    return (
      <>
        <ErrorState error={timeline.error} onRetry={() => void timeline.refetch()} />
        <p className="hint">The timeline needs a timeline result for this site. In fixture mode only Connecting Ridge has one.</p>
      </>
    );
  }
  if (!timeline.data || !data) return <Loading label="Calculating the lunar day..." />;

  const tl = timeline.data;
  const h = Math.min(sliderHours, max);
  const v = skyView(conditions.data, tl, h);
  const nowText = v.sky ? formatUtc(v.sky.t_utc) : formatUtc(card.startUtc);

  return (
    <>
      <div className="page-head">
        <h1>{tl.site.name}: one lunar day</h1>
        <p>Drag the slider or press Play. The Sun and Earth move on the horizon, and the bars show when you have sunlight, a line of sight to Earth, and both.</p>
      </div>
      <WarningList warnings={tl.warnings} />
      <div className="cols-sky">
        <section className="panel stack" aria-labelledby="tl-sky">
          <h2 id="tl-sky">Horizon</h2>
          <HorizonView profile={v.profile} sun={v.sun} earth={v.earth} sunTrail={v.sunTrail} earthTrail={v.earthTrail} />
          <div className="row" style={{ justifyContent: "space-between" }}>
            <button className="btn primary" onClick={() => (h >= max ? (setSlider(0), setPlaying(true)) : setPlaying(!playing))}>
              {playing ? "Pause" : "Play"}
            </button>
            <div className="simtime" aria-live="off">
              {nowText} · day {(h / 24).toFixed(1)}
            </div>
          </div>
          <input
            id="timeline-slider"
            type="range"
            min={0}
            max={max}
            step={1}
            value={h}
            aria-label="Time since landing, in hours"
            onChange={(e) => {
              setPlaying(false);
              setSlider(Number(e.target.value));
            }}
          />
        </section>
        <div className="stack">
          <Countdown body="sun" countdown={tl.countdown.sun} nextEvents={tl.next_events} sliderHours={h} up={v.sun?.up} />
          <Countdown body="earth" countdown={tl.countdown.earth} nextEvents={tl.next_events} sliderHours={h} up={v.earth?.up} />
          <section className="panel">
            <h2>Power now</h2>
            <PowerReadout now={tl.now} sky={v.sky} />
          </section>
        </div>
      </div>
      <section className="panel stack" aria-labelledby="bars-h">
        <h2 id="bars-h">When do we have power, comms, or both?</h2>
        <WindowBars windows={tl.windows} windowHours={max} sliderHours={h} metrics={tl.metrics} onSeek={(hh) => (setPlaying(false), setSlider(hh))} />
        <p className="hint">Click or drag on the bars to jump in time. Earth visibility is geometric line of sight only, not a radio link budget.</p>
      </section>
    </>
  );
}

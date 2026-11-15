import type { Metrics, Windows } from "../api/types";
import { formatValue } from "../lib/format";
import { barSegments } from "../lib/windows";

interface Props {
  windows: Windows;
  windowHours: number;
  sliderHours: number;
  metrics?: Pick<Metrics, "sunlight_pct" | "earth_visibility_pct" | "power_and_comms_pct">;
  onSeek?: (hours: number) => void;
}

const ROWS = [
  { key: "sunlit", label: "Sunlight", cls: "sun" },
  { key: "earth_visible", label: "Earth visible", cls: "earth" },
  { key: "power_and_comms", label: "Power + comms", cls: "both" },
] as const;

export function WindowBars({ windows, windowHours, sliderHours, metrics, onSeek }: Props) {
  const pct = metrics ? [metrics.sunlight_pct, metrics.earth_visibility_pct, metrics.power_and_comms_pct] : [];
  const seek = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!onSeek) return;
    const r = e.currentTarget.getBoundingClientRect();
    onSeek(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * windowHours);
  };
  const days: number[] = [];
  for (let d = 0; d * 24 <= windowHours; d += 7) days.push(d);
  return (
    <div>
      <div className="bars">
        <div className="bars-labels">
          {ROWS.map((r) => (
            <div key={r.key}>{r.label}</div>
          ))}
        </div>
        <div
          className="bars-tracks"
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            seek(e);
          }}
          onPointerMove={(e) => e.buttons === 1 && seek(e)}
        >
          {ROWS.map((r) => (
            <div className="bar" key={r.key}>
              {barSegments(windows[r.key], windowHours).map((s, i) => (
                <div
                  key={i}
                  title={s.duration_text}
                  className={`seg-bar ${r.cls}${s.open_start ? " open-start" : ""}${s.open_end ? " open-end" : ""}`}
                  style={{ left: `${s.left * 100}%`, width: `${s.width * 100}%` }}
                />
              ))}
            </div>
          ))}
          <div className="cursor" style={{ left: `${Math.min(1, sliderHours / windowHours) * 100}%` }} />
        </div>
        <div className="bars-pct">
          {ROWS.map((r, i) => (
            <div key={r.key}>{pct[i] === undefined ? "" : formatValue(pct[i], "%", 0)}</div>
          ))}
        </div>
      </div>
      <div className="bars" style={{ marginTop: 0 }}>
        <div className="bars-labels" aria-hidden="true">
          <div style={{ height: 0 }} />
        </div>
        <div className="axis">
          {days.map((d) => (
            <span key={d} style={{ left: `${((d * 24) / windowHours) * 100}%` }}>
              day {d}
            </span>
          ))}
        </div>
        <div />
      </div>
    </div>
  );
}

import type { DateSweepRow } from "../api/types";

export type SweepKey = "power_and_comms_pct" | "sunlight_pct" | "earth_visibility_pct";

interface Props {
  rows: DateSweepRow[];
  metric: SweepKey;
  selected: number | null;
  onSelect: (i: number) => void;
}

/** One horizontal bar per start date. Plain SVG: no chart library needed. Bars run 0-100 %. */
export function SweepChart({ rows, metric, selected, onSelect }: Props) {
  const W = 640, ROW = 26, L = 92, R = 48, H = rows.length * ROW + 8;
  const x = (v: number) => L + (Math.min(100, Math.max(0, v)) / 100) * (W - L - R);
  return (
    <svg className="sky" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Bar chart: one bar per landing date">
      {[0, 25, 50, 75, 100].map((v) => (
        <line key={v} x1={x(v)} x2={x(v)} y1={0} y2={H} stroke="rgba(190,210,255,0.12)" />
      ))}
      {rows.map((r, i) => {
        const v = r.metrics[metric];
        const y = 4 + i * ROW;
        return (
          <g key={r.label} onClick={() => onSelect(i)} style={{ cursor: "pointer" }}>
            <rect x={0} y={y - 2} width={W} height={ROW - 2} fill={selected === i ? "rgba(51,240,213,0.1)" : "transparent"} />
            <text x={L - 8} y={y + 14} textAnchor="end">{r.label}</text>
            <rect x={L} y={y + 2} width={Math.max(1, x(v) - L)} height={ROW - 10} rx={3} fill={selected === i ? "#33f0d5" : "#5aa8ff"} />
            <text x={x(v) + 6} y={y + 14}>{v.toFixed(0)}%</text>
          </g>
        );
      })}
    </svg>
  );
}

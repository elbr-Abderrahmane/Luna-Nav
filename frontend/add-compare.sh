#!/usr/bin/env bash
# LunaNav frontend: Compare screen + Date sweep screen.
# Run from INSIDE frontend/, after add-screens.sh. Safe to run twice.
set -e
if [ ! -f src/screens/Timeline.tsx ] || [ ! -f src/App.tsx ]; then
  echo "Run add-screens.sh first (src/screens/Timeline.tsx not found), from inside frontend/."; exit 1
fi
STUB='export {};'
is_stub() { [ ! -s "$1" ] || [ "$(cat "$1")" = "$STUB" ]; }
put() { # write only if missing/empty/stub, never overwrite your own work
  local f="$1"; mkdir -p "$(dirname "$f")"
  if [ ! -e "$f" ] || is_stub "$f"; then cat > "$f"; echo "wrote $f"; else cat > /dev/null; echo "kept your version: $f"; fi
}

put src/lib/metrics.ts <<'EOF'
import type { CompareKey } from "../api/types";

export const METRICS: { key: CompareKey; label: string; unit: string; digits: number }[] = [
  { key: "power_and_comms_pct", label: "Power + comms", unit: "%", digits: 0 },
  { key: "sunlight_pct", label: "Sunlight", unit: "%", digits: 0 },
  { key: "earth_visibility_pct", label: "Earth visible", unit: "%", digits: 0 },
  { key: "longest_darkness_h", label: "Longest night", unit: "h", digits: 0 },
  { key: "longest_comms_gap_h", label: "Longest comms gap", unit: "h", digits: 0 },
  { key: "vertical_panel_energy_kwh_m2", label: "Vertical panel energy", unit: "kWh/m2", digits: 0 },
  { key: "sun_elevation_deg_max", label: "Max Sun elevation", unit: "deg", digits: 1 },
];

export const VERDICT_TEXT = { viable: "Viable", marginal: "Marginal", not_viable: "Not viable" } as const;
EOF

put src/components/VerdictBadge.tsx <<'EOF'
import type { Verdict } from "../api/types";
import { VERDICT_TEXT } from "../lib/metrics";

/** The verdict comes from the API (P4's rule). The frontend only displays it, with its reasons. */
export function VerdictBadge({ verdict }: { verdict: Verdict | undefined }) {
  if (!verdict) return <span className="badge">No verdict</span>;
  const cls = verdict.level === "viable" ? "ok" : verdict.level === "marginal" ? "warn" : "bad";
  return <span className={`badge ${cls}`}>{VERDICT_TEXT[verdict.level] ?? verdict.level}</span>;
}
EOF

put src/components/CompareTable.tsx <<'EOF'
import type { Compare } from "../api/types";
import { formatValue } from "../lib/format";
import { METRICS } from "../lib/metrics";
import { VerdictBadge } from "./VerdictBadge";

interface Props {
  data: Compare;
  onOpen: (index: number) => void;
  onSweep: (index: number) => void;
  canSweep: (index: number) => boolean;
}

export function CompareTable({ data, onOpen, onSweep, canSweep }: Props) {
  return (
    <div className="table-wrap">
      <table className="cmp">
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">Metric</span></th>
            {data.rows.map((r, i) => (
              <th scope="col" key={r.label + i}>
                <div>{r.site.name}</div>
                <div className="muted small">{r.start_utc.slice(0, 10)}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Verdict</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                <VerdictBadge verdict={r.verdict} />
                {r.verdict && <p className="hint">{r.verdict.summary}</p>}
                {r.verdict && r.verdict.reasons.length > 0 && (
                  <ul className="reasons">
                    {r.verdict.reasons.map((x, j) => (
                      <li key={j}>{x}</li>
                    ))}
                  </ul>
                )}
              </td>
            ))}
          </tr>
          {METRICS.map((m) => (
            <tr key={m.key}>
              <th scope="row">{m.label}</th>
              {data.rows.map((r, i) => {
                const best = data.best?.[m.key]?.label === r.label;
                return (
                  <td key={i} className={`mono${best ? " best" : ""}`}>
                    {formatValue(r.metrics[m.key as keyof typeof r.metrics] as number | null, m.unit, m.digits)}
                    {best && <span className="best-tag"> best</span>}
                  </td>
                );
              })}
            </tr>
          ))}
          <tr>
            <th scope="row">Horizon method</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                <span className={`badge ${r.method === "horizon_mask" ? "ok" : "warn"}`}>{r.method === "horizon_mask" ? "Terrain" : "Smooth sphere"}</span>
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Warnings</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                {r.warnings.length === 0 ? <span className="muted">None</span> : (
                  <ul className="reasons warn-text">
                    {r.warnings.map((w, j) => (
                      <li key={j}>{w}</li>
                    ))}
                  </ul>
                )}
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row"><span className="sr-only">Actions</span></th>
            {data.rows.map((_r, i) => (
              <td key={i}>
                <div className="stack" style={{ gap: 6 }}>
                  <button className="btn small" onClick={() => onOpen(i)}>Site view</button>
                  <button className="btn small" disabled={!canSweep(i)} onClick={() => onSweep(i)} title={canSweep(i) ? "" : "Date sweep needs a catalog site"}>
                    Try other dates
                  </button>
                </div>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
EOF

put src/components/SweepChart.tsx <<'EOF'
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
EOF

put src/screens/Compare.tsx <<'EOF'
import { useCompare } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { CompareTable } from "../components/CompareTable";
import { ErrorState } from "../components/ErrorState";
import { Loading } from "../components/Loading";
import { WarningList } from "../components/WarningList";
import { MIN_CARDS } from "../lib/constants";
import { useScenarioStore } from "../state/scenarioStore";

export function Compare({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);
  const q = useCompare(cards);

  if (cards.length < MIN_CARDS) {
    return (
      <section className="panel empty">
        <h1>Compare</h1>
        <p className="muted">Add at least {MIN_CARDS} scenarios to compare them.</p>
        <button className="btn primary" onClick={() => onNavigate("builder")}>Go to Scenarios</button>
      </section>
    );
  }
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />;
  if (!q.data) return <Loading label="Comparing scenarios..." />;
  const data = q.data;

  return (
    <>
      <div className="page-head">
        <h1>Compare {data.n_scenarios} scenarios</h1>
        <p>Each column is one site on one landing date. "Best" marks the best value in each row.</p>
      </div>
      <WarningList warnings={data.warnings} />
      <section className="panel">
        <CompareTable
          data={data}
          onOpen={(i) => {
            if (cards[i]) setActive(cards[i].id);
            onNavigate("site");
          }}
          canSweep={(i) => typeof cards[i]?.site === "string"}
          onSweep={(i) => {
            const s = cards[i]?.site;
            if (typeof s === "string") {
              setSweepSite(s);
              onNavigate("sweep");
            }
          }}
        />
      </section>
      <details className="panel">
        <summary>Limits of these numbers</summary>
        <ul>
          {data.limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      </details>
    </>
  );
}
EOF

put src/screens/DateSweep.tsx <<'EOF'
import { useState } from "react";
import { useDateSweep, useSites } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { ErrorState } from "../components/ErrorState";
import { Loading } from "../components/Loading";
import { SweepChart, type SweepKey } from "../components/SweepChart";
import { VerdictBadge } from "../components/VerdictBadge";
import { WarningList } from "../components/WarningList";
import { MAX_CARDS } from "../lib/constants";
import { formatValue } from "../lib/format";
import { useScenarioStore } from "../state/scenarioStore";

const OPTIONS: { key: SweepKey; label: string }[] = [
  { key: "power_and_comms_pct", label: "Power + comms" },
  { key: "sunlight_pct", label: "Sunlight" },
  { key: "earth_visibility_pct", label: "Earth visible" },
];

export function DateSweep({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const sweepSite = useScenarioStore((s) => s.sweepSiteId);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);
  const addCard = useScenarioStore((s) => s.addCard);
  const catalog = useSites().data?.sites;
  const [metric, setMetric] = useState<SweepKey>("power_and_comms_pct");
  const [sel, setSel] = useState<number | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const first = cards.find((c) => c.site === sweepSite)?.startUtc ?? cards[0]?.startUtc ?? "2027-01-10T00:00:00Z";
  const q = useDateSweep(sweepSite, first);

  if (!sweepSite) {
    const options = cards.filter((c): c is typeof c & { site: string } => typeof c.site === "string");
    return (
      <section className="panel empty">
        <h1>Date sweep</h1>
        <p className="muted">Pick a site to see how 12 consecutive lunar days compare.</p>
        <div className="row">
          {options.map((c) => (
            <button key={c.id} className="btn" onClick={() => setSweepSite(c.site)}>
              {catalog?.find((s) => s.id === c.site)?.name ?? c.site}
            </button>
          ))}
        </div>
        {options.length === 0 && <button className="btn primary" onClick={() => onNavigate("builder")}>Go to Scenarios</button>}
      </section>
    );
  }
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />;
  if (!q.data) return <Loading label="Sweeping 12 lunar days..." />;
  const d = q.data;
  const row = sel !== null ? d.rows[sel] : null;
  const bestPc = d.best?.power_and_comms_pct;

  return (
    <>
      <div className="page-head">
        <h1>{d.site.name}: which date is best?</h1>
        <p>Same site, {d.rows.length} landing dates, one lunar day apart. The best date for power + comms is {bestPc ? bestPc.label : "not available"}.</p>
      </div>
      <WarningList warnings={d.warnings} />
      <div className="cols">
        <section className="panel stack">
          <h2>Landing date</h2>
          <div className="seg" role="group" aria-label="Metric">
            {OPTIONS.map((o) => (
              <button key={o.key} aria-pressed={metric === o.key} onClick={() => setMetric(o.key)}>{o.label}</button>
            ))}
          </div>
          <SweepChart rows={d.rows} metric={metric} selected={sel} onSelect={setSel} />
          <p className="hint">Click a bar to select a date.</p>
        </section>
        <section className="panel stack">
          <h2>{row ? row.label : "Selected date"}</h2>
          {!row && <p className="hint">Nothing selected yet.</p>}
          {row && (
            <>
              <VerdictBadge verdict={row.verdict} />
              {row.verdict && <p className="hint">{row.verdict.summary}</p>}
              <dl className="stats">
                <div><dt>Power + comms</dt><dd>{formatValue(row.metrics.power_and_comms_pct, "%", 0)}</dd></div>
                <div><dt>Sunlight</dt><dd>{formatValue(row.metrics.sunlight_pct, "%", 0)}</dd></div>
                <div><dt>Earth visible</dt><dd>{formatValue(row.metrics.earth_visibility_pct, "%", 0)}</dd></div>
                <div><dt>Longest night</dt><dd>{formatValue(row.metrics.longest_darkness_h, "h", 0)}</dd></div>
              </dl>
              {row.warnings.length > 0 && <WarningList warnings={row.warnings} />}
              {note && <p className="hint bad">{note}</p>}
              <div className="row">
                <button
                  className="btn primary"
                  onClick={() => {
                    const id = addCard({ site: sweepSite, startUtc: row.start_utc, label: row.label });
                    if (id) { setNote(null); onNavigate("builder"); }
                    else setNote(`You already have ${MAX_CARDS} scenarios. Remove one first.`);
                  }}
                >
                  Add as scenario
                </button>
              </div>
            </>
          )}
        </section>
      </div>
    </>
  );
}
EOF

# ---------- styles (appended once) ----------
if ! grep -q "lunanav-compare" src/index.css; then cat >> src/index.css <<'EOF'

/* lunanav-compare */
.table-wrap { overflow-x: auto; }
table.cmp { width: 100%; border-collapse: collapse; min-width: 560px; }
table.cmp th, table.cmp td { text-align: left; vertical-align: top; padding: 10px 12px; border-top: 1px solid var(--line); }
table.cmp thead th { border-top: 0; font-size: 15px; }
table.cmp tbody th { font-weight: 500; color: var(--mute); font-size: 13px; width: 170px; }
table.cmp td.best { color: var(--accent); background: rgba(51, 240, 213, 0.07); }
.best-tag { font: 600 10px var(--font-ui); text-transform: uppercase; letter-spacing: 0.1em; }
.small { font-size: 12px; }
.reasons { margin: 6px 0 0; padding-left: 18px; font-size: 13px; color: var(--mute); }
.warn-text { color: var(--warn); }
.badge.bad { color: var(--bad); border-color: var(--bad); }
.stack > .badge { align-self: flex-start; }
EOF
echo "added compare styles to src/index.css"; fi

# ---------- wire into App.tsx (only if the placeholders are still there) ----------
node -e '
const fs=require("fs");let s=fs.readFileSync("src/App.tsx","utf8");
if(s.includes("<ComingNext")){
 s=s.replace(/import \{ ScenarioBuilder \}[^\n]*\n/,m=>m+"import { Compare } from \"./screens/Compare\";\nimport { DateSweep } from \"./screens/DateSweep\";\n");
 s=s.replace(/\{screen === "compare" && <ComingNext name="Compare" \/>\}/,"{screen === \"compare\" && <Compare onNavigate={setScreen} />}");
 s=s.replace(/\{screen === "sweep" && <ComingNext name="Date sweep" \/>\}/,"{screen === \"sweep\" && <DateSweep onNavigate={setScreen} />}");
 s=s.replace(/function ComingNext[\s\S]*?\n\}\n\n/,"");
 fs.writeFileSync("src/App.tsx",s);console.log("wired Compare and Date sweep into src/App.tsx");
}'
echo; echo "Done. Run: npm run dev   then: Scenarios -> Add the 4-site demo set -> Compare tab."

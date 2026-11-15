import type { Compare, CompareRow } from "../api/types";
import { formatValue } from "../lib/format";
import { METRICS } from "../lib/metrics";
import { VerdictBadge } from "./VerdictBadge";

interface Props {
  data: Compare;
  onOpen: (index: number) => void;
  onSweep: (index: number) => void;
  canSweep: (index: number) => boolean;
}

function renderThresholdChecks(row: CompareRow) {
  const t = row.verdict?.thresholds;
  if (!t) return null;
  const m = row.metrics;

  const sunMin = t.sunlight_pct_min ?? t.viable_sunlight_pct_min ?? 60;
  const sunHard = t.sunlight_pct_not_viable ?? t.not_viable_sunlight_pct_below ?? 30;
  const darkMax = t.longest_darkness_h_max ?? t.viable_longest_darkness_h_max ?? 50;
  const darkHard = t.longest_darkness_h_not_viable ?? t.not_viable_longest_darkness_h_above ?? 100;
  const earthMin = t.earth_visibility_pct_min ?? t.viable_earth_visibility_pct_min ?? 50;
  const earthHard = t.earth_visibility_pct_not_viable ?? t.not_viable_earth_visibility_pct_below ?? 20;
  const commsMax = t.longest_comms_gap_h_max ?? t.viable_longest_comms_gap_h_max ?? 72;

  const sunOk = m.sunlight_pct >= sunMin;
  const sunFatal = m.sunlight_pct < sunHard;

  const darkOk = m.longest_darkness_h <= darkMax;
  const darkFatal = m.longest_darkness_h > darkHard;

  const earthOk = m.earth_visibility_pct >= earthMin;
  const earthFatal = m.earth_visibility_pct < earthHard;

  const commsOk = m.longest_comms_gap_h <= commsMax;

  const passedCount = [sunOk, darkOk, earthOk, commsOk].filter(Boolean).length;

  const itemStyle = (ok: boolean, fatal = false): React.CSSProperties => ({
    color: ok ? "var(--ok)" : fatal ? "var(--bad)" : "var(--warn)",
    fontSize: "12px",
    lineHeight: 1.4,
  });

  return (
    <div style={{ marginTop: 8, paddingTop: 6, borderTop: "1px dashed var(--line)" }}>
      <div className="mono muted small" style={{ marginBottom: 4 }}>
        Hardware checks: <strong>{passedCount}/4 targets met</strong>
      </div>
      <ul className="reasons" style={{ margin: 0, listStyle: "none", paddingLeft: 0 }}>
        <li style={itemStyle(sunOk, sunFatal)}>
          {sunOk ? "✓" : sunFatal ? "✗" : "⚠"} Sunlight {Math.round(m.sunlight_pct)}% (target &ge; {sunMin}%)
        </li>
        <li style={itemStyle(darkOk, darkFatal)}>
          {darkOk ? "✓" : darkFatal ? "✗" : "⚠"} Night {Math.round(m.longest_darkness_h)}h (target &le; {darkMax}h, max {darkHard}h)
        </li>
        <li style={itemStyle(earthOk, earthFatal)}>
          {earthOk ? "✓" : earthFatal ? "✗" : "⚠"} Earth vis {Math.round(m.earth_visibility_pct)}% (target &ge; {earthMin}%)
        </li>
        <li style={itemStyle(commsOk, false)}>
          {commsOk ? "✓" : "⚠"} Comms gap {Math.round(m.longest_comms_gap_h)}h (limit &le; {commsMax}h)
        </li>
      </ul>
    </div>
  );
}

export function CompareTable({ data, onOpen, onSweep, canSweep }: Props) {
  const weights = data.ranking?.weights ?? {};
  const rankingList = data.ranking?.ranking ?? [];
  const winShares = data.sensitivity?.random_weights?.top_win_share_pct ?? {};
  const profileName = data.ranking?.profile === "science" ? "Science (Solar)" : "Engineering (Ops)";

  const getRankEntry = (label: string, index: number) => {
    return (
      rankingList.find((item) => item.label === label) ??
      rankingList.find((item) => item.label.startsWith(label)) ??
      rankingList[index]
    );
  };

  return (
    <div className="table-wrap">
      <table className="cmp">
        <thead>
          <tr>
            <th scope="col">
              <span className="sr-only">Metric</span>
            </th>
            {data.rows.map((r, i) => {
              const rankEntry = getRankEntry(r.label, i);
              const isTop = rankEntry?.topsis_rank === 1;
              return (
                <th scope="col" key={r.label + i}>
                  <div className="row" style={{ gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                    <span>{r.site.name}</span>
                    {rankEntry?.topsis_rank !== undefined && (
                      <span className={`badge ${isTop ? "ok" : ""}`}>
                        #{rankEntry.topsis_rank} {isTop ? `Top (${profileName})` : ""}
                      </span>
                    )}
                  </div>
                  <div className="muted small">{r.start_utc.slice(0, 10)}</div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rankingList.length > 0 && (
            <tr>
              <th scope="row">
                <div>Decision rank</div>
                <div className="muted small">{profileName}</div>
              </th>
              {data.rows.map((r, i) => {
                const entry = getRankEntry(r.label, i);
                if (!entry) return <td key={i}>—</td>;
                const isFirst = entry.topsis_rank === 1;
                const topsisPct = entry.topsis_score !== undefined ? `${(entry.topsis_score * 100).toFixed(1)} %` : "—";
                const wsmPct = entry.wsm_score !== undefined ? `${(entry.wsm_score * 100).toFixed(1)} %` : "—";
                const winShare = winShares[entry.label];
                return (
                  <td key={i} className={isFirst ? "best" : ""}>
                    <div className="row" style={{ gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                      <span className={`badge ${isFirst ? "ok" : ""}`}>
                        Rank #{entry.topsis_rank ?? "—"}
                      </span>
                      <span className="mono" style={{ fontWeight: 600 }}>
                        TOPSIS {topsisPct}
                      </span>
                      {isFirst && <span className="best-tag"> winner</span>}
                    </div>
                    <div className="hint" style={{ marginTop: 4 }}>
                      WSM: <span className="mono">{wsmPct}</span> (Rank #{entry.wsm_rank ?? "—"})
                      {winShare !== undefined && (
                        <>
                          {" · "}Monte-Carlo win: <span className="mono">{winShare.toFixed(0)} %</span>
                        </>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>
          )}
          <tr>
            <th scope="row">Verdict</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                <VerdictBadge verdict={r.verdict} />
                {r.verdict && <p className="hint">{r.verdict.summary}</p>}
                {renderThresholdChecks(r)}
              </td>
            ))}
          </tr>
          {METRICS.map((m) => {
            const wt = weights[m.key];
            return (
              <tr key={m.key}>
                <th scope="row">
                  <div className="row" style={{ justifyContent: "space-between", alignItems: "center", gap: 6 }}>
                    <span>{m.label}</span>
                    {wt !== undefined && (
                      <span
                        className="mono muted small"
                        style={{
                          padding: "1px 6px",
                          borderRadius: 4,
                          background: wt >= 0.2 ? "rgba(51, 240, 213, 0.14)" : "rgba(255, 255, 255, 0.05)",
                          color: wt >= 0.2 ? "var(--accent)" : undefined,
                          fontSize: "0.75rem",
                        }}
                        title={`Weight in ${profileName} profile`}
                      >
                        {Math.round(wt * 100)}% wt
                      </span>
                    )}
                  </div>
                </th>
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
            );
          })}
          <tr>
            <th scope="row">Horizon method</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                <span className={`badge ${r.method === "horizon_mask" ? "ok" : "warn"}`}>
                  {r.method === "horizon_mask" ? "Terrain" : "Smooth sphere"}
                </span>
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Warnings</th>
            {data.rows.map((r, i) => (
              <td key={i}>
                {r.warnings.length === 0 ? (
                  <span className="muted">None</span>
                ) : (
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
            <th scope="row">
              <span className="sr-only">Actions</span>
            </th>
            {data.rows.map((_r, i) => (
              <td key={i}>
                <div className="stack" style={{ gap: 6 }}>
                  <button className="btn small" onClick={() => onOpen(i)}>
                    Site view
                  </button>
                  <button
                    className="btn small"
                    disabled={!canSweep(i)}
                    onClick={() => onSweep(i)}
                    title={canSweep(i) ? "" : "Date sweep needs a catalog site"}
                  >
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

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

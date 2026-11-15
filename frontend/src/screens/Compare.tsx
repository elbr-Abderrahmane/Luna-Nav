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

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lunanav_comparison.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = () => {
    const headers = [
      "label", "site_name", "start_utc", "verdict", "sunlight_pct",
      "longest_darkness_h", "earth_visibility_pct", "longest_comms_gap_h",
      "power_and_comms_pct", "vertical_panel_energy_kwh_m2",
    ];
    const lines = [
      headers.join(","),
      ...data.rows.map((r) =>
        [
          JSON.stringify(r.label),
          JSON.stringify(r.site.name),
          JSON.stringify(r.start_utc),
          JSON.stringify(r.verdict?.level ?? ""),
          r.metrics.sunlight_pct,
          r.metrics.longest_darkness_h,
          r.metrics.earth_visibility_pct,
          r.metrics.longest_comms_gap_h,
          r.metrics.power_and_comms_pct,
          r.metrics.vertical_panel_energy_kwh_m2,
        ].join(",")
      ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lunanav_comparison.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="page-head">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1>Compare {data.n_scenarios} scenarios</h1>
            <p>Each column is one site on one landing date. "Best" marks the best value in each row.</p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn small" onClick={exportCsv}>Export CSV</button>
            <button className="btn small" onClick={exportJson}>Export JSON</button>
          </div>
        </div>
      </div>
      <WarningList warnings={data.warnings} />
      {data.explanation && (
        <section className="panel" aria-label="Decision summary">
          <h2>Decision summary</h2>
          <p>{data.explanation}</p>
        </section>
      )}
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
      {data.ranking && (
        <details className="panel">
          <summary>Multi-criteria ranking (WSM & TOPSIS) & weight sensitivity</summary>
          {data.ranking_explanation && <p className="hint" style={{ marginTop: 8 }}>{data.ranking_explanation}</p>}
          <div className="table-wrap" style={{ marginTop: 8 }}>
            <table className="cmp">
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">Scenario</th>
                  <th scope="col">TOPSIS score</th>
                  <th scope="col">WSM score</th>
                  <th scope="col">Win probability (Monte Carlo)</th>
                </tr>
              </thead>
              <tbody>
                {data.ranking.ranking.map((entry, idx) => (
                  <tr key={entry.label}>
                    <td className="mono">#{entry.topsis_rank ?? entry.wsm_rank ?? idx + 1}</td>
                    <td>{entry.label}</td>
                    <td className="mono">{entry.topsis_score !== undefined ? (entry.topsis_score * 100).toFixed(1) + "%" : "—"}</td>
                    <td className="mono">{entry.wsm_score !== undefined ? (entry.wsm_score * 100).toFixed(1) + "%" : "—"}</td>
                    <td className="mono">
                      {data.sensitivity?.random_weights.top_win_share_pct[entry.label] !== undefined
                        ? data.sensitivity.random_weights.top_win_share_pct[entry.label].toFixed(1) + "%"
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
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

import { useState } from "react";
import { useCompare } from "../api/queries";
import type { RankingProfile } from "../api/types";
import type { Screen } from "../components/AppShell";
import { CompareTable } from "../components/CompareTable";
import { ErrorState } from "../components/ErrorState";
import { Loading } from "../components/Loading";
import { Seg } from "../components/Seg";
import { WarningList } from "../components/WarningList";
import { MIN_CARDS } from "../lib/constants";
import { useScenarioStore } from "../state/scenarioStore";

const DEFAULT_THRESHOLDS: Record<string, number> = {
  viable_sunlight_pct_min: 60,
  viable_longest_darkness_h_max: 50,
  not_viable_longest_darkness_h_above: 100,
  viable_earth_visibility_pct_min: 50,
  viable_longest_comms_gap_h_max: 72,
};

export function Compare({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);

  const [profile, setProfile] = useState<RankingProfile>("engineering");
  const [draftThresholds, setDraftThresholds] = useState<Record<string, number>>(DEFAULT_THRESHOLDS);
  const [appliedThresholds, setAppliedThresholds] = useState<Record<string, number> | undefined>(undefined);

  const q = useCompare(cards, profile, appliedThresholds);

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

  const updateDraft = (key: string, val: string) => {
    const num = Number(val);
    if (!Number.isNaN(num)) {
      setDraftThresholds((prev) => ({ ...prev, [key]: num }));
    }
  };

  return (
    <>
      <div className="page-head">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1>Compare {data.n_scenarios} scenarios</h1>
            <p>Each column is one site on one landing date. "Best" marks the best value in each row.</p>
          </div>
          <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
            <Seg
              label="Ranking profile"
              value={profile}
              onChange={setProfile}
              options={[
                { value: "engineering", label: "Engineering (Ops)" },
                { value: "science", label: "Science (Solar)" },
              ]}
            />
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
      <details className="panel">
        <summary>
          Spacecraft hardware & viability thresholds{" "}
          {appliedThresholds ? <span className="badge warn" style={{ marginLeft: 8 }}>Custom active</span> : <span className="muted small">(Default rules)</span>}
        </summary>
        <p className="hint" style={{ marginTop: 8 }}>
          Adjust battery survival and direct-to-Earth communication limits to see how spacecraft hardware changes each scenario's verdict.
        </p>
        <div className="row" style={{ gap: 16, flexWrap: "wrap", marginTop: 10, alignItems: "flex-end" }}>
          <label className="stack" style={{ gap: 4 }}>
            <span className="small muted">Min viable sunlight (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              value={draftThresholds.viable_sunlight_pct_min}
              onChange={(e) => updateDraft("viable_sunlight_pct_min", e.target.value)}
              style={{ width: 110 }}
            />
          </label>
          <label className="stack" style={{ gap: 4 }}>
            <span className="small muted">Max viable night (h)</span>
            <input
              type="number"
              min={0}
              max={700}
              value={draftThresholds.viable_longest_darkness_h_max}
              onChange={(e) => updateDraft("viable_longest_darkness_h_max", e.target.value)}
              style={{ width: 110 }}
            />
          </label>
          <label className="stack" style={{ gap: 4 }}>
            <span className="small muted">Hard battery night limit (h)</span>
            <input
              type="number"
              min={1}
              max={700}
              value={draftThresholds.not_viable_longest_darkness_h_above}
              onChange={(e) => updateDraft("not_viable_longest_darkness_h_above", e.target.value)}
              style={{ width: 130 }}
            />
          </label>
          <label className="stack" style={{ gap: 4 }}>
            <span className="small muted">Min viable Earth vis (%)</span>
            <input
              type="number"
              min={0}
              max={100}
              value={draftThresholds.viable_earth_visibility_pct_min}
              onChange={(e) => updateDraft("viable_earth_visibility_pct_min", e.target.value)}
              style={{ width: 110 }}
            />
          </label>
          <label className="stack" style={{ gap: 4 }}>
            <span className="small muted">Max comms gap (h)</span>
            <input
              type="number"
              min={0}
              max={700}
              value={draftThresholds.viable_longest_comms_gap_h_max}
              onChange={(e) => updateDraft("viable_longest_comms_gap_h_max", e.target.value)}
              style={{ width: 110 }}
            />
          </label>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn primary small" onClick={() => setAppliedThresholds({ ...draftThresholds })}>
              Apply thresholds
            </button>
            {appliedThresholds && (
              <button
                className="btn small"
                onClick={() => {
                  setDraftThresholds(DEFAULT_THRESHOLDS);
                  setAppliedThresholds(undefined);
                }}
              >
                Reset defaults
              </button>
            )}
          </div>
        </div>
      </details>
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
        <details className="panel" open>
          <summary>
            Multi-criteria ranking (WSM & TOPSIS — {data.ranking.profile} profile) & weight sensitivity
          </summary>
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

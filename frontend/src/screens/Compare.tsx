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
import { compareCsv, copyText, downloadText, summaryText } from "../lib/export";
import { useScenarioStore } from "../state/scenarioStore";

const DEFAULT_THRESHOLDS: Record<string, number> = {
  sunlight_pct_min: 60,
  longest_darkness_h_max: 50,
  longest_darkness_h_not_viable: 100,
  earth_visibility_pct_min: 50,
  longest_comms_gap_h_max: 72,
};

export function Compare({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);

  const [profile, setProfile] = useState<RankingProfile>("engineering");
  const [draftThresholds, setDraftThresholds] = useState<Record<string, number>>(DEFAULT_THRESHOLDS);
  const [appliedThresholds, setAppliedThresholds] = useState<Record<string, number> | undefined>(undefined);
  const [note, setNote] = useState<string | null>(null);

  const q = useCompare(cards, profile, appliedThresholds);

  if (cards.length < MIN_CARDS) {
    return (
      <section className="panel empty">
        <h1>Compare</h1>
        <p className="muted">Add at least {MIN_CARDS} scenarios to compare them.</p>
        <button className="btn primary" onClick={() => onNavigate("builder")}>
          Go to Scenarios
        </button>
      </section>
    );
  }
  if (q.isError) return <ErrorState error={q.error} onRetry={() => void q.refetch()} />;
  if (!q.data) return <Loading label="Comparing scenarios..." />;
  const data = q.data;

  const updateDraft = (key: string, val: string) => {
    const num = Number(val);
    if (!Number.isNaN(num)) {
      setDraftThresholds((prev) => ({ ...prev, [key]: num }));
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>Compare {data.n_scenarios} scenarios</h1>
        <p title={data.ranking_explanation}>
          {data.ranking_explanation ??
            'Each column is one site on one landing date. "Best" marks the best value in each row.'}
        </p>
        <div className="row export-bar">
          <Seg
            label="Ranking profile"
            value={profile}
            onChange={setProfile}
            options={[
              { value: "engineering", label: "Engineering (Ops)" },
              { value: "science", label: "Science (Solar)" },
            ]}
          />
          <button
            className="btn small"
            onClick={() => {
              downloadText("lunanav-comparison.csv", compareCsv(data));
              setNote("Saved lunanav-comparison.csv");
            }}
          >
            Download CSV
          </button>
          <button
            className="btn small"
            onClick={() =>
              void copyText(summaryText(data)).then((ok) =>
                setNote(ok ? "Summary copied" : "Could not copy: your browser blocked the clipboard")
              )
            }
          >
            Copy summary
          </button>
          {note && (
            <span className="hint" role="status">
              {note}
            </span>
          )}
        </div>
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
      <div className="row" style={{ gap: 12, flexWrap: "wrap", alignItems: "flex-start" }}>
        <details className="panel" style={{ flex: "1 1 380px" }}>
          <summary>
            Customize Spacecraft Hardware Thresholds {appliedThresholds ? "(Custom Active)" : "(NASA Default)"}
          </summary>
          <div className="stack" style={{ marginTop: 10 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                gap: 8,
              }}
            >
              <label className="field">
                <span>Min Viable Sunlight (%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={draftThresholds.sunlight_pct_min}
                  onChange={(e) => updateDraft("sunlight_pct_min", e.target.value)}
                />
              </label>
              <label className="field">
                <span>Max Viable Darkness (h)</span>
                <input
                  type="number"
                  min={0}
                  max={708}
                  value={draftThresholds.longest_darkness_h_max}
                  onChange={(e) => updateDraft("longest_darkness_h_max", e.target.value)}
                />
              </label>
              <label className="field">
                <span>Survival Limit Darkness (h)</span>
                <input
                  type="number"
                  min={0}
                  max={708}
                  value={draftThresholds.longest_darkness_h_not_viable}
                  onChange={(e) => updateDraft("longest_darkness_h_not_viable", e.target.value)}
                />
              </label>
              <label className="field">
                <span>Min Viable Earth Vis (%)</span>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={draftThresholds.earth_visibility_pct_min}
                  onChange={(e) => updateDraft("earth_visibility_pct_min", e.target.value)}
                />
              </label>
              <label className="field">
                <span>Max Viable Comms Gap (h)</span>
                <input
                  type="number"
                  min={0}
                  max={708}
                  value={draftThresholds.longest_comms_gap_h_max}
                  onChange={(e) => updateDraft("longest_comms_gap_h_max", e.target.value)}
                />
              </label>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <button className="btn primary small" onClick={() => setAppliedThresholds({ ...draftThresholds })}>
                Apply Thresholds
              </button>
              {appliedThresholds && (
                <button
                  className="btn small"
                  onClick={() => {
                    setDraftThresholds(DEFAULT_THRESHOLDS);
                    setAppliedThresholds(undefined);
                  }}
                >
                  Reset to NASA Defaults
                </button>
              )}
            </div>
          </div>
        </details>
        <details className="panel" style={{ flex: "1 1 320px" }}>
          <summary>Limits of these numbers</summary>
          <ul>
            {data.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </details>
      </div>
    </>
  );
}

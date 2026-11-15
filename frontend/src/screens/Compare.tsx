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

const HARDWARE_PRESETS: {
  id: string;
  label: string;
  desc: string;
  thresholds: Record<string, number> | undefined;
}[] = [
  {
    id: "default",
    label: "Solar + Direct Radio (Default)",
    desc: "4-day battery (50h target / 100h survival), direct-to-Earth comms (≥50% Earth vis, ≤72h gap).",
    thresholds: undefined,
  },
  {
    id: "relay",
    label: "+ Lunar Relay Satellite",
    desc: "Orbiter relay removes direct-Earth comms bottleneck (0% direct Earth required, 708h gap allowed).",
    thresholds: {
      sunlight_pct_min: 60,
      longest_darkness_h_max: 50,
      longest_darkness_h_not_viable: 100,
      earth_visibility_pct_min: 0,
      longest_comms_gap_h_max: 708,
    },
  },
  {
    id: "rtg",
    label: "+ RTG / 14-Day Night Battery",
    desc: "Radioisotope heater/power survives 250h–350h lunar nights with direct-to-Earth radio.",
    thresholds: {
      sunlight_pct_min: 45,
      longest_darkness_h_max: 250,
      longest_darkness_h_not_viable: 350,
      earth_visibility_pct_min: 50,
      longest_comms_gap_h_max: 72,
    },
  },
  {
    id: "all-weather",
    label: "Nuclear + Relay (All-Weather)",
    desc: "Both RTG night survival (≤300h) and lunar relay satellite comms.",
    thresholds: {
      sunlight_pct_min: 40,
      longest_darkness_h_max: 300,
      longest_darkness_h_not_viable: 350,
      earth_visibility_pct_min: 0,
      longest_comms_gap_h_max: 708,
    },
  },
];

function sanitizeThresholds(raw: Record<string, number>): Record<string, number> {
  const sunlightMin = Math.min(100, Math.max(0, Number(raw.sunlight_pct_min ?? 60)));
  const darknessMax = Math.max(0, Number(raw.longest_darkness_h_max ?? 50));
  const darknessHard = Math.max(darknessMax, Number(raw.longest_darkness_h_not_viable ?? 100));
  const earthMin = Math.min(100, Math.max(0, Number(raw.earth_visibility_pct_min ?? 50)));
  const commsMax = Math.max(0, Number(raw.longest_comms_gap_h_max ?? 72));
  return {
    sunlight_pct_min: sunlightMin,
    sunlight_pct_not_viable: Math.min(30, sunlightMin),
    longest_darkness_h_max: darknessMax,
    longest_darkness_h_not_viable: darknessHard,
    earth_visibility_pct_min: earthMin,
    earth_visibility_pct_not_viable: Math.min(20, earthMin),
    longest_comms_gap_h_max: commsMax,
  };
}

export function Compare({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);

  const [profile, setProfile] = useState<RankingProfile>("engineering");
  const [activePreset, setActivePreset] = useState<string>("default");
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
  if (q.isError) {
    return (
      <ErrorState
        error={q.error}
        onRetry={() => {
          if (appliedThresholds) {
            setActivePreset("default");
            setDraftThresholds(DEFAULT_THRESHOLDS);
            setAppliedThresholds(undefined);
          } else {
            void q.refetch();
          }
        }}
      />
    );
  }
  if (!q.data) return <Loading label="Comparing scenarios..." />;
  const data = q.data;

  const updateDraft = (key: string, val: string) => {
    const num = Number(val);
    if (!Number.isNaN(num)) {
      setDraftThresholds((prev) => ({ ...prev, [key]: num }));
    }
  };

  const applyPreset = (presetId: string) => {
    const p = HARDWARE_PRESETS.find((x) => x.id === presetId);
    if (!p) return;
    setActivePreset(p.id);
    if (!p.thresholds) {
      setDraftThresholds(DEFAULT_THRESHOLDS);
      setAppliedThresholds(undefined);
      setNote(`Hardware preset: ${p.label}`);
    } else {
      setDraftThresholds(p.thresholds);
      setAppliedThresholds(sanitizeThresholds(p.thresholds));
      setNote(`Hardware preset: ${p.label}`);
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
      <section className="panel strip" aria-label="Spacecraft hardware thresholds and limits">
        <div className="row" style={{ gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <span className="muted small">Spacecraft hardware:</span>
          {HARDWARE_PRESETS.map((p) => (
            <button
              key={p.id}
              className="chip"
              aria-pressed={activePreset === p.id}
              title={p.desc}
              onClick={() => applyPreset(p.id)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="row" style={{ gap: "1.25rem", flexWrap: "wrap" }}>
          <details className="pop">
            <summary>
              Customize Spacecraft Hardware Thresholds{" "}
              {appliedThresholds ? `(${activePreset === "custom" ? "Custom" : activePreset} active)` : "(NASA Default)"}
            </summary>
            <div className="pop-body">
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <p style={{ margin: 0, fontSize: 12, color: "var(--mute)" }}>
                  Set your lander&apos;s battery and radio limits to re-evaluate each site&apos;s{" "}
                  <strong>Verdict (Viable / Marginal / Not viable)</strong> and <strong>Hardware Checks (X/4)</strong>:
                </p>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(175px, 1fr))",
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
                  <button
                    className="btn primary small"
                    onClick={() => {
                      const clean = sanitizeThresholds(draftThresholds);
                      setActivePreset("custom");
                      setDraftThresholds({
                        sunlight_pct_min: clean.sunlight_pct_min,
                        longest_darkness_h_max: clean.longest_darkness_h_max,
                        longest_darkness_h_not_viable: clean.longest_darkness_h_not_viable,
                        earth_visibility_pct_min: clean.earth_visibility_pct_min,
                        longest_comms_gap_h_max: clean.longest_comms_gap_h_max,
                      });
                      setAppliedThresholds(clean);
                      setNote("Applied custom spacecraft thresholds");
                    }}
                  >
                    Apply Thresholds
                  </button>
                  {appliedThresholds && (
                    <button className="btn small" onClick={() => applyPreset("default")}>
                      Reset to NASA Defaults
                    </button>
                  )}
                </div>
              </div>
            </div>
          </details>
          <details className="pop">
            <summary>Limits of these numbers</summary>
            <div className="pop-body">
              <ul>
                {data.limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </div>
          </details>
        </div>
      </section>
    </>
  );
}

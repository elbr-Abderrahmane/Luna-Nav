import { useState } from "react";
import { useCompare } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { CompareTable } from "../components/CompareTable";
import { ErrorState } from "../components/ErrorState";
import { Loading } from "../components/Loading";
import { WarningList } from "../components/WarningList";
import { MIN_CARDS } from "../lib/constants";
import { compareCsv, copyText, downloadText, summaryText } from "../lib/export";
import { useScenarioStore } from "../state/scenarioStore";

export function Compare({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);
  const q = useCompare(cards);
  const [note, setNote] = useState<string | null>(null);

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
        <div className="row export-bar">
          <button className="btn small" onClick={() => { downloadText("lunanav-comparison.csv", compareCsv(data)); setNote("Saved lunanav-comparison.csv"); }}>
            Download CSV
          </button>
          <button
            className="btn small"
            onClick={() => void copyText(summaryText(data)).then((ok) => setNote(ok ? "Summary copied" : "Could not copy: your browser blocked the clipboard"))}
          >
            Copy summary
          </button>
          {note && <span className="hint" role="status">{note}</span>}
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

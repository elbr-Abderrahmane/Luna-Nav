import { useState } from "react";
import { Seg } from "../components/Seg";
import { useDateSweep, useSites } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { ErrorState } from "../components/ErrorState";
import { Loading } from "../components/Loading";
import { SweepChart, type SweepKey } from "../components/SweepChart";
import { VerdictBadge } from "../components/VerdictBadge";
import { WarningList } from "../components/WarningList";
import { MAX_CARDS } from "../lib/constants";
import { formatValue } from "../lib/format";
import { siteLabel } from "../lib/site";
import { useScenarioStore } from "../state/scenarioStore";

const OPTIONS: { key: SweepKey; label: string }[] = [
  { key: "power_and_comms_pct", label: "Power + comms" },
  { key: "sunlight_pct", label: "Sunlight" },
  { key: "earth_visibility_pct", label: "Earth visible" },
];

export function DateSweep({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const storedSweepSite = useScenarioStore((s) => s.sweepSiteId);
  const sweepSite = storedSweepSite && cards.some((c) => c.site === storedSweepSite) ? storedSweepSite : null;
  const setSweepSite = useScenarioStore((s) => s.setSweepSiteId);
  const addCard = useScenarioStore((s) => s.addCard);
  const catalog = useSites().data?.sites;
  const [metric, setMetric] = useState<SweepKey>("power_and_comms_pct");
  const [sel, setSel] = useState<number | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const siteCards = cards.filter((c, i) => typeof c.site === "string" && cards.findIndex((x) => x.site === c.site) === i);
  const switcher = (
    <div className="sweep-sites sweep-sites-bar" role="group" aria-label="Site to sweep">
      <span className="muted">Site</span>
      {siteCards.map((c) => (
        <button key={c.id} className="chip" aria-pressed={c.site === sweepSite} onClick={() => { setSweepSite(c.site as string); setSel(null); }}>
          {siteLabel(c.site, catalog)}
        </button>
      ))}
      {cards.some((c) => typeof c.site !== "string") && <span className="hint">Scenarios with typed coordinates cannot be swept.</span>}
    </div>
  );
  const first = cards.find((c) => c.site === sweepSite)?.startUtc ?? cards[0]?.startUtc ?? "2027-01-10T00:00:00Z";
  const q = useDateSweep(sweepSite, first);

  if (!sweepSite) {
    const options = cards.filter((c): c is typeof c & { site: string } => typeof c.site === "string");
    return (
      <section className="panel empty">
        <h1>Date sweep</h1>
        <p className="muted">{options.length > 0 ? "Pick a site to see how 12 consecutive lunar days compare." : "Add a scenario first, then come back to sweep its dates."}</p>
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
  if (q.isError) return <>{switcher}<ErrorState error={q.error} onRetry={() => void q.refetch()} /></>;
  if (!q.data) return <>{switcher}<Loading label="Sweeping 12 lunar days..." /></>;
  const d = q.data;
  const row = sel !== null ? d.rows[sel] : null;
  const bestPc = d.best?.power_and_comms_pct;

  return (
    <>
      <div className="page-head">
        <h1>{d.site.name}: which date is best?</h1>
        <p>Same site, {d.rows.length} landing dates, one lunar day apart. The best date for power + comms is {bestPc ? bestPc.label : "not available"}.</p>
      </div>
      {switcher}
      <WarningList warnings={d.warnings} />
      <div className="cols">
        <section className="panel stack">
          <h2>Landing date</h2>
          <Seg label="Metric" value={metric} onChange={setMetric} options={OPTIONS.map((o) => ({ value: o.key, label: o.label }))} />
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

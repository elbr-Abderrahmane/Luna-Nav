import { useSites } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { Countdown } from "../components/Countdown";
import { ErrorState } from "../components/ErrorState";
import { ExternalLinks } from "../components/ExternalLinks";
import { HorizonView } from "../components/HorizonView";
import { Loading } from "../components/Loading";
import { PowerReadout } from "../components/PowerReadout";
import { TerrainCard } from "../components/TerrainCard";
import { VerdictBadge } from "../components/VerdictBadge";
import { WarningList } from "../components/WarningList";
import { siteLabel } from "../lib/site";
import { formatUtc } from "../lib/utc";
import { skyView, useActive } from "../state/useActive";

export function SiteView({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const { card, conditions, timeline } = useActive();
  const catalog = useSites().data?.sites;

  if (!card) {
    return (
      <section className="panel empty">
        <h1>No scenario selected</h1>
        <p className="muted">Add a scenario first, then open its site view.</p>
        <button className="btn primary" onClick={() => onNavigate("builder")}>
          Go to Scenarios
        </button>
      </section>
    );
  }

  const data = conditions.data ?? timeline.data;
  if (!data) {
    if (conditions.isError) return <ErrorState error={conditions.error} onRetry={() => void conditions.refetch()} />;
    return <Loading />;
  }
  const v = skyView(conditions.data, timeline.data, 0);
  const name = data.site.name ?? siteLabel(card.site, catalog);

  return (
    <>
      <div className="page-head">
        <h1>{name}</h1>
        <div className="row">
          <span className="muted">Landing {formatUtc(card.startUtc)}</span>
          <span className={`badge ${data.method === "horizon_mask" ? "ok" : "warn"}`}>
            {data.method === "horizon_mask" ? "Terrain horizon (LOLA DEM)" : "Smooth-sphere horizon, no terrain data"}
          </span>
          {data.verdict && <VerdictBadge verdict={data.verdict} />}
        </div>
      </div>
      <WarningList warnings={data.warnings} />
      <div className="cols-sky">
        <section className="panel stack" aria-labelledby="sky-h">
          <h2 id="sky-h">Sun and Earth over the horizon, at landing</h2>
          <HorizonView profile={v.profile} sun={v.sun} earth={v.earth} sunTrail={v.sunTrail} earthTrail={v.earthTrail} />
          <div className="row sky-foot">
            {timeline.isError ? (
              <p className="hint warn">Terrain skyline unavailable: {(timeline.error as Error).message}</p>
            ) : (
              <p className="hint">Faint dots show where the Sun and Earth move during the whole window.</p>
            )}
            <button className="btn primary" onClick={() => onNavigate("timeline")}>
              Open the timeline
            </button>
          </div>
        </section>
        <div className="stack side">
          <Countdown body="sun" countdown={data.countdown.sun} nextEvents={data.next_events} sliderHours={0} up={v.sun?.up} />
          <Countdown body="earth" countdown={data.countdown.earth} nextEvents={data.next_events} sliderHours={0} up={v.earth?.up} />
          <section className="panel">
            <h2>Power at landing</h2>
            <PowerReadout now={data.now} sky={null} />
          </section>
        </div>
      </div>
      <section className="panel strip" aria-label="Real site and method">
        <ExternalLinks site={data.site} />
        <div className="row" style={{ gap: "1rem", flexWrap: "wrap" }}>
          <details className="pop">
            <summary>Local Terrain &amp; Slope (LOLA DEM)</summary>
            <div className="pop-body">
              <TerrainCard site={data.site} terrain={data.terrain} />
            </div>
          </details>
          <details className="pop">
            <summary>How these numbers are made</summary>
            <div className="pop-body">
              <ul>
                <li>Ephemeris: {data.data_sources.ephemeris_source}</li>
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

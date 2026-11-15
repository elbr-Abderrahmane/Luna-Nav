import { useConditions } from "../api/queries";
import type { Site } from "../api/types";
import { formatValue } from "../lib/format";
import { siteLabel } from "../lib/site";
import { dateOnly, utcFromParts } from "../lib/time";
import type { ScenarioCard as Card } from "../state/scenarioStore";

interface Props {
  card: Card;
  catalog: Site[] | undefined;
  active: boolean;
  onOpen: () => void;
  onRemove: () => void;
  onDate: (utc: string) => void;
}

export function ScenarioCard({ card, catalog, active, onOpen, onRemove, onDate }: Props) {
  const q = useConditions(card);
  const m = q.data?.metrics;
  const name = siteLabel(card.site, catalog);
  return (
    <article className={`card${active ? " card-active" : ""}`}>
      <header className="card-head">
        <h3>{name}</h3>
        <button className="btn small" onClick={onRemove} aria-label={`Remove ${name}`}>
          Remove
        </button>
      </header>
      <div className="card-meta">
        <label className="field-inline">
          Landing date (UTC)
          <input type="date" value={dateOnly(card.startUtc)} onChange={(e) => e.target.value && onDate(utcFromParts(e.target.value))} />
        </label>
        <span className="muted">{card.windowDays ? `${card.windowDays} days` : "One lunar day"}</span>
      </div>
      {q.isLoading && <div className="muted">Calculating...</div>}
      {q.isError && <div className="hint warn">{(q.error as Error).message}</div>}
      {m && (
        <dl className="mini">
          <div>
            <dt>Sunlight</dt>
            <dd>{formatValue(m.sunlight_pct, "%", 0)}</dd>
          </div>
          <div>
            <dt>Earth visible</dt>
            <dd>{formatValue(m.earth_visibility_pct, "%", 0)}</dd>
          </div>
          <div>
            <dt>Longest night</dt>
            <dd>{formatValue(m.longest_darkness_h, "h", 0)}</dd>
          </div>
        </dl>
      )}
      <div>
        <button className="btn" onClick={onOpen}>
          Open site view
        </button>
      </div>
    </article>
  );
}

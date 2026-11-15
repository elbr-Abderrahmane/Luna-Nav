import { useMemo, useState } from "react";
import { useSites } from "../api/queries";
import type { Site } from "../api/types";
import { ErrorState } from "./ErrorState";
import { Loading } from "./Loading";

const CATEGORY_LABEL: Record<string, string> = {
  apollo: "Apollo",
  artemis: "Artemis",
  clps: "CLPS",
  international: "International",
  south_pole_candidate: "South pole candidates",
  reference: "Reference",
};

export function SitePicker({ value, onChange }: { value: string | null; onChange: (id: string) => void }) {
  const { data, isLoading, error, refetch } = useSites();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const sites: Site[] = useMemo(() => (data?.sites ?? []).filter((s) => s.id), [data]);
  const categories = useMemo(() => Array.from(new Set(sites.map((s) => s.category))), [sites]);
  const shown = useMemo(() => {
    const t = query.trim().toLowerCase();
    return sites.filter(
      (s) => (category === "all" || s.category === category) && (!t || [s.name, s.id, s.mission, s.agency].some((v) => v?.toLowerCase().includes(t))),
    );
  }, [sites, query, category]);

  if (isLoading) return <Loading label="Loading the site catalog..." />;
  if (error) return <ErrorState error={error} onRetry={() => void refetch()} />;

  return (
    <div className="stack">
      <label className="field">
        <span>Search {sites.length} sites</span>
        <input id="site-search" type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Name, mission or agency" />
      </label>
      <div className="chips" role="group" aria-label="Filter by category">
        <button className="chip" aria-pressed={category === "all"} onClick={() => setCategory("all")}>
          All
        </button>
        {categories.map((c) => (
          <button key={c} className="chip" aria-pressed={category === c} onClick={() => setCategory(c)}>
            {CATEGORY_LABEL[c] ?? c}
          </button>
        ))}
      </div>
      <ul className="site-list">
        {shown.length === 0 && <li className="hint" style={{ padding: 10 }}>No site matches.</li>}
        {shown.map((s) => (
          <li key={s.id}>
            <button className="site-item" aria-pressed={value === s.id} onClick={() => s.id && onChange(s.id)}>
              <span>{s.name}</span>
              <small>
                {[s.mission, s.agency].filter(Boolean).join(" · ") || CATEGORY_LABEL[s.category] || s.category} · {s.lat_deg.toFixed(2)}, {s.lon_deg.toFixed(2)}
              </small>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

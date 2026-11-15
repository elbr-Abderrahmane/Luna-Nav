import { useState } from "react";
import { useSites } from "../api/queries";
import { siteLabel } from "../lib/site";
import { useScenarioStore } from "../state/scenarioStore";
import type { Screen } from "./AppShell";

const KEY = "lunanav.rail";

/** Switch between your scenarios without going back to the builder. Collapsible. */
export function ScenarioRail({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const activeId = useScenarioStore((s) => s.activeCardId);
  const setActive = useScenarioStore((s) => s.setActiveCard);
  const catalog = useSites().data?.sites;
  const [open, setOpen] = useState(() => {
    try { return localStorage.getItem(KEY) !== "0"; } catch { return true; }
  });
  const toggle = () => {
    setOpen(!open);
    try { localStorage.setItem(KEY, open ? "0" : "1"); } catch { /* storage can be blocked */ }
  };
  return (
    <aside className={`rail${open ? "" : " rail-closed"}`} aria-label="Scenarios">
      <div className="rail-head">
        {open && <h2>Scenarios</h2>}
        <button className="rail-toggle" onClick={toggle} aria-expanded={open} aria-label={open ? "Collapse scenarios" : "Expand scenarios"}>
          {open ? "‹" : "›"}
        </button>
      </div>
      <ul>
        {cards.map((c, i) => {
          const name = siteLabel(c.site, catalog);
          return (
            <li key={c.id}>
              <button className="rail-item" aria-current={c.id === activeId ? "true" : undefined} title={name} onClick={() => setActive(c.id)}>
                <span className="rail-n">{i + 1}</span>
                {open && (
                  <span className="rail-text">
                    <span>{name}</span>
                    <small>{c.startUtc.slice(0, 10)}</small>
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
      {open && (
        <button className="btn small" onClick={() => onNavigate("builder")}>
          + Add scenario
        </button>
      )}
    </aside>
  );
}

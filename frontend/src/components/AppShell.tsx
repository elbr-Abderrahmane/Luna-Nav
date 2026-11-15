import { useState, type ReactNode } from "react";
import { USE_FIXTURES } from "../api/client";
import { useScenarioStore } from "../state/scenarioStore";
import { Assistant } from "./Assistant";
import { LunaLogo } from "./LunaLogo";
import { ScenarioRail } from "./ScenarioRail";
import { Starfield } from "./Starfield";

export type Screen = "builder" | "site" | "timeline" | "compare" | "sweep";

const STEPS: { id: Screen; label: string }[] = [
  { id: "builder", label: "Scenarios" },
  { id: "site", label: "Site view" },
  { id: "timeline", label: "Timeline" },
  { id: "compare", label: "Compare" },
  { id: "sweep", label: "Date sweep" },
];

const BANNER_KEY = "lunanav.hideFixtureBanner";

export function AppShell({ screen, onNavigate, children }: { screen: Screen; onNavigate: (s: Screen) => void; children: ReactNode }) {
  const hasCards = useScenarioStore((s) => s.cards.length > 0);
  const [hideBanner, setHideBanner] = useState(() => {
    try { return localStorage.getItem(BANNER_KEY) === "1"; } catch { return false; }
  });
  const here = STEPS.findIndex((s) => s.id === screen);
  const prev = here > 0 ? STEPS[here - 1] : null;
  const next = here >= 0 && here < STEPS.length - 1 ? STEPS[here + 1] : null;
  const showRail = hasCards && (screen === "site" || screen === "timeline");

  return (
    <div className="app">
      <Starfield />
      <header className="topbar">
        <div className="brand" style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: "12px" }}>
          <LunaLogo size={36} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span className="brand-name">LunaNav</span>
            <span className="brand-tag">If we land here, on this date, will we have power and comms?</span>
          </div>
        </div>
        <div className="pager" role="group" aria-label="Previous and next screen">
          <button className="pager-btn" disabled={!prev} onClick={() => prev && onNavigate(prev.id)} aria-label={prev ? `Back to ${prev.label}` : "No previous screen"} title={prev ? `Back: ${prev.label}` : ""}>
            ‹
          </button>
          <button className="pager-btn" disabled={!next} onClick={() => next && onNavigate(next.id)} aria-label={next ? `Next: ${next.label}` : "No next screen"} title={next ? `Next: ${next.label}` : ""}>
            ›
          </button>
        </div>
        <nav className="flow" aria-label="Screens">
          <ol>
            {STEPS.map((s, i) => (
              <li key={s.id} className="flow-item" data-state={i < here ? "done" : i === here ? "current" : "todo"}>
                {i > 0 && <span className="flow-link" aria-hidden="true" />}
                <button className="flow-node" aria-current={i === here ? "page" : undefined} onClick={() => onNavigate(s.id)}>
                  <span className="orb" aria-hidden="true" />
                  <span className="flow-label">{s.label}</span>
                </button>
              </li>
            ))}
          </ol>
          <button className="flow-loop" onClick={() => onNavigate("builder")} title="Start another scenario">
            <span aria-hidden="true">↺</span> New scenario
          </button>
        </nav>
      </header>
      {USE_FIXTURES && !hideBanner && (
        <div className="fixture-banner" role="status">
          <span>
            Fixture mode: these are saved example runs. The date you pick does not change the numbers, and only a few sites have data.
          </span>
          <button
            className="btn small"
            onClick={() => {
              setHideBanner(true);
              try { localStorage.setItem(BANNER_KEY, "1"); } catch { /* storage can be blocked */ }
            }}
          >
            Hide
          </button>
        </div>
      )}
      <Assistant screen={screen} onNavigate={onNavigate} />
      <div className={`workspace${showRail ? " with-rail" : ""}`}>
        {showRail && <ScenarioRail onNavigate={onNavigate} />}
        <main key={screen} className="page enter">
          {children}
        </main>
      </div>
    </div>
  );
}

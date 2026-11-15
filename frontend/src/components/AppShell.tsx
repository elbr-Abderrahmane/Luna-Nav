import type { ReactNode } from "react";
import { USE_FIXTURES } from "../api/client";
import { Starfield } from "./Starfield";

export type Screen = "builder" | "site" | "timeline" | "compare" | "sweep";

const STEPS: { id: Screen; label: string }[] = [
  { id: "builder", label: "Scenarios" },
  { id: "site", label: "Site view" },
  { id: "timeline", label: "Timeline" },
  { id: "compare", label: "Compare" },
  { id: "sweep", label: "Date sweep" },
];

export function AppShell({ screen, onNavigate, children }: { screen: Screen; onNavigate: (s: Screen) => void; children: ReactNode }) {
  return (
    <div className="app">
      <Starfield />
      <header className="topbar">
        <div className="brand">
          <span className="brand-name">LunaNav</span>
          <span className="brand-tag">If we land here, on this date, will we have power and comms?</span>
        </div>
        <nav className="steps" aria-label="Screens">
          {STEPS.map((s, i) => (
            <button key={s.id} className="step" aria-current={screen === s.id ? "page" : undefined} onClick={() => onNavigate(s.id)}>
              <span className="step-n">{i + 1}</span>
              {s.label}
            </button>
          ))}
        </nav>
      </header>
      {USE_FIXTURES && (
        <div className="fixture-banner" role="status">
          Fixture mode: these are saved example runs. The date you pick does not change the numbers, and only a few sites have data. Set VITE_USE_FIXTURES=false to use the live API.
        </div>
      )}
      <main className="page">{children}</main>
    </div>
  );
}

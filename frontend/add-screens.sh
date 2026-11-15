#!/usr/bin/env bash
# LunaNav frontend: first screens (shell, Scenario builder, Site view, Timeline).
# Run from INSIDE frontend/, AFTER setup-structure.sh. Safe to run more than once:
#  - fills empty stub files,
#  - replaces the Vite starter App.tsx / index.css (the old ones go to .old-scaffold/),
#  - never overwrites a file that already has your own content.
set -e

if [ ! -f package.json ] || [ ! -d src/api ]; then
  echo "Run this from inside frontend/ after setup-structure.sh (src/api not found)."
  exit 1
fi

STUB='export {};'
BACKUP='.old-scaffold'
is_stub() { [ ! -s "$1" ] || [ "$(cat "$1")" = "$STUB" ]; }

# put FILE [REGEX]: new content on stdin. Writes if the file is missing/empty/stub,
# or if it matches REGEX (the Vite starter). Otherwise keeps your version.
put() {
  local f="$1" sig="$2"
  mkdir -p "$(dirname "$f")"
  if [ ! -e "$f" ] || is_stub "$f"; then cat > "$f"; echo "wrote $f"
  elif [ -n "$sig" ] && grep -Eq "$sig" "$f"; then
    mkdir -p "$BACKUP/$(dirname "$f")"; mv "$f" "$BACKUP/$f"; cat > "$f"; echo "replaced starter file (backup in $BACKUP/): $f"
  else cat > /dev/null; echo "kept your version: $f"; fi
}

# ---------- types: the real site catalog has `status` and `notes`, and no elevation_m ----------
if grep -q 'coord_quality: "landed"' src/api/types.ts && ! grep -q 'notes: string | null' src/api/types.ts; then
  node -e '
const fs=require("fs");let s=fs.readFileSync("src/api/types.ts","utf8");
s=s.replace(/(coord_quality: "landed" \| "approximate" \| "exact" \| "user_input";\n  lat_deg: number;\n  lon_deg: number;\n)  elevation_m: number;\n/,
 "$1  /** Missing in the sites.json catalog; present in the Site returned with conditions. */\n  elevation_m?: number;\n  /** Catalog only: reference | candidate | landed | planned ... (checked against mock_data/astro/sites.json) */\n  status?: string;\n  notes?: string | null;\n");
fs.writeFileSync("src/api/types.ts",s);console.log("updated Site type in src/api/types.ts");'
fi

# ---------- theme ----------
put src/index.css 'color-scheme: light dark|Vite' <<'EOF'
/* lunanav-screens: space theme. One dark look on purpose. */
:root {
  --void: #04060d;
  --panel: rgba(9, 14, 28, 0.78);
  --line: rgba(190, 210, 255, 0.18);
  --line-strong: rgba(190, 210, 255, 0.36);
  --fg: #e8eefc;
  --mute: #93a1bf;
  --sun: #ffcf6b;
  --earth: #5aa8ff;
  --accent: #33f0d5;
  --ok: #4fd6a0;
  --warn: #ffb454;
  --bad: #ff6b6b;
  --font-ui: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html, body, #root { min-height: 100%; }
body { margin: 0; background: var(--void); color: var(--fg); font: 15px/1.5 var(--font-ui); }
button, input, select { font: inherit; color: inherit; }
button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible { outline: 2px solid var(--sun); outline-offset: 2px; }
a { color: var(--accent); }
h1, h2, h3 { margin: 0; line-height: 1.2; text-wrap: balance; }
h1 { font-size: clamp(22px, 3vw, 30px); }
h2 { font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--mute); font-weight: 600; }
h3 { font-size: 16px; }
.muted { color: var(--mute); }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

.starfield { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
.app { position: relative; z-index: 1; min-height: 100vh; display: flex; flex-direction: column; }
.topbar { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 24px; padding: 12px 24px; border-bottom: 1px solid var(--line); background: rgba(4, 6, 13, 0.78); backdrop-filter: blur(6px); }
.brand { display: flex; flex-direction: column; min-width: 0; }
.brand-name { font-size: 19px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.brand-tag { font-size: 12px; color: var(--mute); }
.steps { display: flex; flex-wrap: wrap; gap: 6px; }
.step { display: flex; align-items: center; gap: 8px; padding: 7px 12px; border: 1px solid var(--line); border-radius: 6px; background: transparent; cursor: pointer; }
.step:hover { border-color: var(--line-strong); }
.step[aria-current="page"] { border-color: var(--accent); color: var(--accent); background: rgba(51, 240, 213, 0.08); }
.step-n { font: 600 11px var(--font-mono); color: var(--mute); }
.fixture-banner { padding: 8px 24px; font-size: 13px; color: var(--warn); background: rgba(255, 180, 84, 0.08); border-bottom: 1px solid rgba(255, 180, 84, 0.3); }
.page { width: 100%; max-width: 1240px; margin: 0 auto; padding: 24px; display: flex; flex-direction: column; gap: 20px; }

.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; min-width: 0; }
.panel > h2 { margin-bottom: 12px; }
.cols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.cols-sky { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.stack { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.page-head { display: flex; flex-direction: column; gap: 6px; }
.page-head p { margin: 0; color: var(--mute); }
@media (max-width: 860px) { .cols, .cols-sky { grid-template-columns: minmax(0, 1fr); } .page { padding: 16px; } .topbar { padding: 12px 16px; } }

.btn { padding: 8px 14px; border: 1px solid var(--line-strong); border-radius: 6px; background: transparent; cursor: pointer; }
.btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #02130f; font-weight: 600; }
.btn.primary:hover:not(:disabled) { background: #7bf7e5; color: #02130f; }
.btn.small { padding: 4px 10px; font-size: 13px; }
.field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.field > span, .field-inline { font-size: 12px; color: var(--mute); }
input[type="text"], input[type="search"], input[type="date"], select { width: 100%; padding: 8px 10px; background: rgba(255, 255, 255, 0.05); border: 1px solid var(--line); border-radius: 6px; }
input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(1) opacity(0.7); }
.field-inline { display: flex; align-items: center; gap: 8px; }
.field-inline input { width: auto; padding: 4px 8px; }
.seg { display: inline-flex; border: 1px solid var(--line-strong); border-radius: 6px; overflow: hidden; }
.seg button { padding: 6px 12px; border: 0; background: transparent; cursor: pointer; }
.seg button[aria-pressed="true"] { background: rgba(51, 240, 213, 0.14); color: var(--accent); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { padding: 3px 10px; border: 1px solid var(--line); border-radius: 999px; background: transparent; cursor: pointer; font-size: 12px; }
.chip[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); }
.hint { font-size: 13px; color: var(--mute); margin: 0; }
.hint.warn { color: var(--warn); }
.hint.bad { color: var(--bad); }

.site-list { list-style: none; margin: 0; padding: 0; max-height: 270px; overflow-y: auto; border: 1px solid var(--line); border-radius: 6px; }
.site-list li + li { border-top: 1px solid var(--line); }
.site-item { display: flex; flex-direction: column; width: 100%; text-align: left; gap: 2px; padding: 8px 10px; border: 0; background: transparent; cursor: pointer; }
.site-item:hover { background: rgba(255, 255, 255, 0.05); }
.site-item[aria-pressed="true"] { background: rgba(51, 240, 213, 0.12); box-shadow: inset 3px 0 0 var(--accent); }
.site-item small { color: var(--mute); }

.cards { display: flex; flex-direction: column; gap: 12px; }
.card { border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 10px; background: rgba(255, 255, 255, 0.03); }
.card-active { border-color: var(--accent); }
.card-head { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
.card-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; }
.mini { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0; }
.mini dt { font-size: 11px; color: var(--mute); text-transform: uppercase; letter-spacing: 0.08em; }
.mini dd { margin: 0; font: 600 15px var(--font-mono); }

.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px; border: 1px solid var(--line-strong); color: var(--mute); }
.badge.ok { color: var(--ok); border-color: var(--ok); }
.badge.warn { color: var(--warn); border-color: var(--warn); }
.banner { margin: 0; padding: 10px 14px 10px 30px; border-radius: 6px; border: 1px solid; font-size: 14px; }
.banner.warn { color: var(--warn); border-color: rgba(255, 180, 84, 0.45); background: rgba(255, 180, 84, 0.07); }
.error { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; padding: 12px 14px; border: 1px solid rgba(255, 107, 107, 0.5); border-radius: 6px; background: rgba(255, 107, 107, 0.07); color: var(--bad); }
.loading { color: var(--mute); padding: 12px 0; }
.empty { text-align: center; padding: 48px 16px; display: flex; flex-direction: column; align-items: center; gap: 12px; }

.sky { width: 100%; height: auto; display: block; }
.sky text { font-family: var(--font-mono); font-size: 11px; fill: var(--mute); }
.sky .lbl-sun { fill: var(--sun); }
.sky .lbl-earth { fill: var(--earth); }

.tile { border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; }
.tile-head { display: flex; align-items: center; gap: 8px; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--mute); }
.dot { width: 9px; height: 9px; border-radius: 50%; }
.tile-sun .dot { background: var(--sun); box-shadow: 0 0 10px var(--sun); }
.tile-earth .dot { background: var(--earth); box-shadow: 0 0 10px var(--earth); }
.tile-event { color: var(--mute); font-size: 14px; }
.tile-time { font: 600 26px/1.15 var(--font-mono); font-variant-numeric: tabular-nums; }
.tile-time.long { font-size: 16px; }
.tile .state { margin-top: 4px; font-size: 12px; }
.state.up { color: var(--ok); }
.state.down { color: var(--mute); }
.stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; }
.stats dt { font-size: 11px; color: var(--mute); text-transform: uppercase; letter-spacing: 0.08em; }
.stats dd { margin: 2px 0 0; font: 600 16px var(--font-mono); font-variant-numeric: tabular-nums; }

.bars { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 0 14px; align-items: stretch; }
.bars-labels, .bars-pct { display: flex; flex-direction: column; gap: 10px; font-size: 13px; }
.bars-labels > div, .bars-pct > div { height: 22px; display: flex; align-items: center; white-space: nowrap; }
.bars-pct { font-family: var(--font-mono); color: var(--mute); }
.bars-tracks { position: relative; display: flex; flex-direction: column; gap: 10px; cursor: ew-resize; touch-action: none; }
.bar { position: relative; height: 22px; background: rgba(255, 255, 255, 0.06); border-radius: 4px; }
.seg-bar { position: absolute; top: 0; bottom: 0; border-radius: 4px; }
.seg-bar.sun { background: var(--sun); }
.seg-bar.earth { background: var(--earth); }
.seg-bar.both { background: var(--accent); }
.seg-bar.open-start { border-top-left-radius: 0; border-bottom-left-radius: 0; }
.seg-bar.open-end { border-top-right-radius: 0; border-bottom-right-radius: 0; }
.cursor { position: absolute; top: -4px; bottom: -4px; width: 2px; background: var(--fg); box-shadow: 0 0 8px var(--fg); pointer-events: none; }
.axis { position: relative; height: 18px; margin-top: 6px; font: 11px var(--font-mono); color: var(--mute); }
.axis span { position: absolute; transform: translateX(-50%); }
input[type="range"] { width: 100%; accent-color: var(--accent); }
.simtime { font: 600 16px var(--font-mono); font-variant-numeric: tabular-nums; }
details summary { cursor: pointer; color: var(--mute); }
details ul { margin: 8px 0 0; padding-left: 20px; color: var(--mute); font-size: 14px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
EOF

# ---------- app ----------
put src/App.tsx 'Vite|viteLogo|reactLogo|useState\(0\)' <<'EOF'
import { useState } from "react";
import { AppShell, type Screen } from "./components/AppShell";
import { Providers } from "./Providers";
import { ScenarioBuilder } from "./screens/ScenarioBuilder";
import { SiteView } from "./screens/SiteView";
import { Timeline } from "./screens/Timeline";

function ComingNext({ name }: { name: string }) {
  return (
    <section className="panel empty">
      <h1>{name}</h1>
      <p className="muted">This screen is built next.</p>
    </section>
  );
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("builder");
  return (
    <Providers>
      <AppShell screen={screen} onNavigate={setScreen}>
        {screen === "builder" && <ScenarioBuilder onNavigate={setScreen} />}
        {screen === "site" && <SiteView onNavigate={setScreen} />}
        {screen === "timeline" && <Timeline onNavigate={setScreen} />}
        {screen === "compare" && <ComingNext name="Compare" />}
        {screen === "sweep" && <ComingNext name="Date sweep" />}
      </AppShell>
    </Providers>
  );
}
EOF

# ---------- small helpers ----------
put src/lib/site.ts '' <<'EOF'
import type { Site, SiteInput } from "../api/types";

/** Display name for a card's site: catalog name, typed name, or the coordinates. */
export function siteLabel(site: SiteInput, catalog?: Site[]): string {
  if (typeof site === "string") return catalog?.find((s) => s.id === site)?.name ?? site;
  return site.name ?? `${site.lat_deg.toFixed(2)}, ${site.lon_deg.toFixed(2)}`;
}

export function parseLatLon(lat: string, lon: string): { ok: true; lat: number; lon: number } | { ok: false; error: string } {
  const la = Number(lat.trim());
  const lo = Number(lon.trim());
  if (lat.trim() === "" || lon.trim() === "") return { ok: false, error: "Enter a latitude and a longitude." };
  if (!Number.isFinite(la) || !Number.isFinite(lo)) return { ok: false, error: "Latitude and longitude must be numbers." };
  if (la < -90 || la > 90) return { ok: false, error: "Latitude must be between -90 and 90 (south pole = -90)." };
  if (lo < -180 || lo > 180) return { ok: false, error: "Longitude must be between -180 and 180 (east is positive)." };
  return { ok: true, lat: la, lon: lo };
}
EOF

put src/lib/utc.ts '' <<'EOF'
/** "2027-01-10T21:36:48Z" -> "2027-01-10 21:36 UTC" */
export const formatUtc = (utc: string): string => utc.slice(0, 16).replace("T", " ") + " UTC";
EOF

# ---------- active card + sky data for the horizon view ----------
put src/state/useActive.ts '' <<'EOF'
import { useConditions, useTimeline } from "../api/queries";
import type { SiteConditions, SiteTimeline } from "../api/types";
import { skyAtHours, type SkyAtSlider } from "../lib/series";
import { useScenarioStore } from "./scenarioStore";

/** The active card and its two results. Conditions are fast; the timeline adds the skyline and the paths. */
export function useActive() {
  const cards = useScenarioStore((s) => s.cards);
  const activeId = useScenarioStore((s) => s.activeCardId);
  const card = cards.find((c) => c.id === activeId) ?? null;
  const conditions = useConditions(card);
  const timeline = useTimeline(card);
  return { card, conditions, timeline };
}

export interface BodyOnSky {
  az: number;
  el: number;
  up: boolean;
}
export interface Trail {
  az: number[];
  el: number[];
}

/** What HorizonView draws for a slider position. At slider 0 it uses the landing-moment numbers. */
export function skyView(conditions: SiteConditions | undefined, timeline: SiteTimeline | undefined, sliderHours: number) {
  const sky: SkyAtSlider | null = timeline && sliderHours > 0 ? skyAtHours(timeline, sliderHours) : null;
  const now = conditions?.now ?? timeline?.now;
  let sun: BodyOnSky | null = null;
  let earth: BodyOnSky | null = null;
  if (sky) {
    sun = { az: sky.sun.azimuth_deg, el: sky.sun.elevation_deg, up: sky.sun.margin_deg > 0 };
    earth = { az: sky.earth.azimuth_deg, el: sky.earth.elevation_deg, up: sky.earth.visible };
  } else if (now) {
    sun = { az: now.sun.azimuth_deg, el: now.sun.elevation_deg, up: now.sun.visible };
    earth = { az: now.earth.azimuth_deg, el: now.earth.elevation_deg, up: now.earth.visible };
  }
  const s = timeline?.series;
  return {
    sky,
    profile: timeline?.horizon_profile ?? null,
    sun,
    earth,
    sunTrail: s ? ({ az: s.sun_azimuth_deg, el: s.sun_elevation_deg } as Trail) : null,
    earthTrail: s ? ({ az: s.earth_azimuth_deg, el: s.earth_elevation_deg } as Trail) : null,
  };
}
EOF

# ---------- components ----------
put src/components/Starfield.tsx '' <<'EOF'
import { useEffect, useRef } from "react";

function rng(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Static starry background, drawn once per window size. */
export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const draw = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = window.innerWidth;
      const h = window.innerHeight;
      c.width = w * dpr;
      c.height = h * dpr;
      c.style.width = `${w}px`;
      c.style.height = `${h}px`;
      const ctx = c.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const r = rng(11);
      const n = Math.round((w * h) / 3200);
      for (let i = 0; i < n; i++) {
        const x = r() * w;
        const y = r() * h;
        const k = r();
        const size = k > 0.97 ? 1.7 : k > 0.85 ? 1.1 : 0.7;
        const tint = r();
        const rgb = tint < 0.15 ? "255,224,190" : tint < 0.35 ? "190,210,255" : "255,255,255";
        ctx.fillStyle = `rgba(${rgb},${(0.3 + 0.7 * r()).toFixed(2)})`;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    };
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, []);
  return <canvas ref={ref} className="starfield" aria-hidden="true" />;
}
EOF

put src/components/AppShell.tsx '' <<'EOF'
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
EOF

put src/components/Loading.tsx '' <<'EOF'
export function Loading({ label = "Calculating..." }: { label?: string }) {
  return (
    <div className="loading" role="status">
      {label}
    </div>
  );
}
EOF

put src/components/ErrorState.tsx '' <<'EOF'
import { ApiError } from "../api/client";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg =
    error instanceof ApiError ? `${error.message} (${error.code})` : error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div className="error" role="alert">
      <strong>Could not load this.</strong>
      <span>{msg}</span>
      {onRetry && (
        <button className="btn small" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
EOF

put src/components/WarningList.tsx '' <<'EOF'
/** API warnings must be visible on the card (README 3, rule 5). */
export function WarningList({ warnings }: { warnings: string[] | undefined }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <ul className="banner warn" role="status">
      {warnings.map((w, i) => (
        <li key={i}>{w}</li>
      ))}
    </ul>
  );
}
EOF

put src/components/SitePicker.tsx '' <<'EOF'
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
EOF

put src/components/LatLonInput.tsx '' <<'EOF'
import { parseLatLon } from "../lib/site";

export interface LatLonValue {
  lat: string;
  lon: string;
  name: string;
}

export function LatLonInput({ value, onChange }: { value: LatLonValue; onChange: (v: LatLonValue) => void }) {
  const parsed = parseLatLon(value.lat, value.lon);
  const touched = value.lat !== "" || value.lon !== "";
  return (
    <div className="stack">
      <div className="cols" style={{ gap: 12 }}>
        <label className="field">
          <span>Latitude (deg, south pole = -90)</span>
          <input id="lat" type="text" inputMode="decimal" value={value.lat} onChange={(e) => onChange({ ...value, lat: e.target.value })} placeholder="-89.45" />
        </label>
        <label className="field">
          <span>Longitude (deg, east positive)</span>
          <input id="lon" type="text" inputMode="decimal" value={value.lon} onChange={(e) => onChange({ ...value, lon: e.target.value })} placeholder="-137.3" />
        </label>
      </div>
      <label className="field">
        <span>Name (optional)</span>
        <input id="site-name" type="text" value={value.name} onChange={(e) => onChange({ ...value, name: e.target.value })} placeholder="My landing site" />
      </label>
      {touched && !parsed.ok && <p className="hint bad">{parsed.error}</p>}
      {parsed.ok && parsed.lat > -80 && (
        <p className="hint warn">North of 80 deg S there is no terrain data. The horizon will be a smooth sphere, which is less accurate.</p>
      )}
    </div>
  );
}
EOF

put src/components/ScenarioCard.tsx '' <<'EOF'
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
EOF

put src/components/HorizonView.tsx '' <<'EOF'
import type { BodyOnSky, Trail } from "../state/useActive";

interface Props {
  /** 360 azimuth bins of the terrain skyline. null = not available (a flat 0 deg line is drawn). */
  profile: { azimuth_deg: number[]; elevation_deg: number[] } | null;
  sun: BodyOnSky | null;
  earth: BodyOnSky | null;
  sunTrail?: Trail | null;
  earthTrail?: Trail | null;
}

// Panorama: azimuth 0-360 left to right (north at both edges), elevation up. Drawing only, no science.
const W = 720;
const H = 300;
const L = 40;
const R = 12;
const T = 14;
const B = 30;
const YMIN = -8;
const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"];

const niceStep = (range: number) => [1, 2, 5, 10, 15, 30].find((s) => range / s <= 6) ?? 30;

export function HorizonView({ profile, sun, earth, sunTrail, earthTrail }: Props) {
  const profileMax = profile && profile.elevation_deg.length ? Math.max(...profile.elevation_deg) : 0;
  const trailMax = Math.max(0, ...(sunTrail?.el ?? []), ...(earthTrail?.el ?? []));
  const top = Math.max(profileMax, sun?.el ?? 0, earth?.el ?? 0, trailMax);
  const ymax = Math.min(90, Math.max(12, Math.ceil(top + 3)));

  const x = (az: number) => L + (az / 360) * (W - L - R);
  const y = (el: number) => {
    const c = Math.min(ymax, Math.max(YMIN, el));
    return H - B - ((c - YMIN) / (ymax - YMIN)) * (H - B - T);
  };

  let line = "";
  if (profile && profile.azimuth_deg.length) {
    profile.azimuth_deg.forEach((a, i) => {
      line += `${i ? "L" : "M"}${x(a).toFixed(1)} ${y(profile.elevation_deg[i]).toFixed(1)}`;
    });
    line += `L${x(360).toFixed(1)} ${y(profile.elevation_deg[0]).toFixed(1)}`;
  } else {
    line = `M${x(0)} ${y(0)}L${x(360)} ${y(0)}`;
  }
  const area = `${line}L${x(360)} ${H - B}L${x(0)} ${H - B}Z`;

  const trailPath = (t?: Trail | null) =>
    t ? t.az.map((a, i) => (t.el[i] >= YMIN ? `M${x(a).toFixed(1)} ${y(t.el[i]).toFixed(1)}h0` : "")).join("") : "";

  const step = niceStep(ymax - 0);
  const yTicks: number[] = [];
  for (let v = 0; v <= ymax; v += step) yTicks.push(v);

  const label = (b: BodyOnSky, name: string, cls: string, r: number, color: string) => {
    const cx = x(b.az);
    const cy = y(b.el);
    const lx = Math.min(W - R - 40, Math.max(L + 40, cx));
    const above = cy > T + 26;
    return (
      <g opacity={b.up ? 1 : 0.4}>
        <circle cx={cx} cy={cy} r={r * 2} style={{ fill: color }} opacity={0.22} />
        <circle cx={cx} cy={cy} r={r} style={{ fill: color }} />
        <text x={lx} y={above ? cy - r * 2 - 4 : cy + r * 2 + 12} textAnchor="middle" className={cls}>
          {b.up ? name : `${name} (below horizon)`}
        </text>
      </g>
    );
  };

  const summary = `Horizon view. ${sun ? `Sun at azimuth ${sun.az.toFixed(0)} degrees, elevation ${sun.el.toFixed(1)} degrees. ` : ""}${earth ? `Earth at azimuth ${earth.az.toFixed(0)} degrees, elevation ${earth.el.toFixed(1)} degrees.` : ""}`;

  return (
    <svg className="sky" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={summary}>
      <defs>
        <linearGradient id="sky-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#070b1a" />
          <stop offset="1" stopColor="#16203f" />
        </linearGradient>
        <linearGradient id="terrain-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3a3f4d" />
          <stop offset="1" stopColor="#14171f" />
        </linearGradient>
      </defs>
      <rect x={L} y={T} width={W - L - R} height={H - B - T} fill="url(#sky-grad)" />
      {yTicks.map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="rgba(190,210,255,0.12)" strokeDasharray={v === 0 ? "5 4" : undefined} />
          <text x={L - 6} y={y(v) + 4} textAnchor="end">{`${v}`}</text>
        </g>
      ))}
      {COMPASS.map((c, i) => (
        <g key={i}>
          <line x1={x(i * 45)} x2={x(i * 45)} y1={H - B} y2={H - B + 4} stroke="rgba(190,210,255,0.4)" />
          <text x={x(i * 45)} y={H - B + 16} textAnchor="middle">{c}</text>
        </g>
      ))}
      <path d={trailPath(sunTrail)} style={{ stroke: "var(--sun)" }} strokeWidth={2} strokeLinecap="round" opacity={0.3} fill="none" />
      <path d={trailPath(earthTrail)} style={{ stroke: "var(--earth)" }} strokeWidth={2} strokeLinecap="round" opacity={0.3} fill="none" />
      <path d={area} fill="url(#terrain-grad)" />
      <path d={line} fill="none" stroke="rgba(214,224,245,0.8)" strokeWidth={1.2} />
      {earth && label(earth, "Earth", "lbl-earth", 6.5, "#5aa8ff")}
      {sun && label(sun, "Sun", "lbl-sun", 8, "#ffcf6b")}
      <text x={W - R} y={T + 12} textAnchor="end">elevation (deg), azimuth from north</text>
    </svg>
  );
}
EOF

put src/components/Countdown.tsx '' <<'EOF'
import type { Countdown as CountdownData, NextEvent } from "../api/types";
import { countdownLabel, liveCountdown, type Body } from "../lib/countdown";

interface Props {
  body: Body;
  countdown: CountdownData;
  nextEvents: NextEvent[];
  sliderHours: number;
  /** is the centre of the disk above the horizon right now (for the state line) */
  up?: boolean;
}

/** "Earthrise in 21 h 37 min": the API's own text at the landing moment, derived from next_events once the slider moves. */
export function Countdown({ body, countdown, nextEvents, sliderHours, up }: Props) {
  // After the slider moves, never show the landing-moment text as if it were current.
  const stale = sliderHours > 0 && !countdown.beyond_window && liveCountdown(body, nextEvents, sliderHours) === null;
  const text = stale ? "No later change in the event list" : countdownLabel(body, countdown, nextEvents, sliderHours);
  const m = text.match(/^(\w+) in (.+)$/);
  return (
    <div className={`tile tile-${body}`}>
      <div className="tile-head">
        <span className="dot" />
        {body === "sun" ? "Sun" : "Earth"}
      </div>
      {m ? (
        <>
          <div className="tile-event">{m[1]} in</div>
          <div className="tile-time">{m[2]}</div>
        </>
      ) : (
        <div className="tile-time long">{text}</div>
      )}
      {up !== undefined && <div className={`state ${up ? "up" : "down"}`}>{up ? "Above the horizon" : "Below the horizon"}</div>}
    </div>
  );
}
EOF

put src/components/PowerReadout.tsx '' <<'EOF'
import type { SiteConditions } from "../api/types";
import { formatValue } from "../lib/format";
import type { SkyAtSlider } from "../lib/series";

/** Power numbers are geometry only: no efficiency, temperature or dust (README 5.4). */
export function PowerReadout({ now, sky }: { now: SiteConditions["now"]; sky: SkyAtSlider | null }) {
  const sunEl = sky ? sky.sun.elevation_deg : now.sun.elevation_deg;
  const margin = sky ? sky.sun.margin_deg : now.sun.margin_above_horizon_deg;
  const irr = sky ? sky.irradiance_w_m2 : now.power.irradiance_w_m2;
  const disk = sky ? sky.sun.disk_visible_fraction : now.sun.disk_visible_fraction;
  return (
    <dl className="stats">
      <div>
        <dt>Sun elevation</dt>
        <dd>{formatValue(sunEl, "deg", 2)}</dd>
      </div>
      <div>
        <dt>Above horizon by</dt>
        <dd>{formatValue(margin, "deg", 2)}</dd>
      </div>
      <div>
        <dt>Sun disk visible</dt>
        <dd>{formatValue(disk * 100, "%", 0)}</dd>
      </div>
      <div>
        <dt>Irradiance</dt>
        <dd>{formatValue(irr, "W/m2", 0)}</dd>
      </div>
      {!sky && (
        <div>
          <dt>Vertical panel, at landing</dt>
          <dd>{formatValue(now.power.vertical_panel_w_m2, "W/m2", 0)}</dd>
        </div>
      )}
    </dl>
  );
}
EOF

put src/components/WindowBars.tsx '' <<'EOF'
import type { Metrics, Windows } from "../api/types";
import { formatValue } from "../lib/format";
import { barSegments } from "../lib/windows";

interface Props {
  windows: Windows;
  windowHours: number;
  sliderHours: number;
  metrics?: Pick<Metrics, "sunlight_pct" | "earth_visibility_pct" | "power_and_comms_pct">;
  onSeek?: (hours: number) => void;
}

const ROWS = [
  { key: "sunlit", label: "Sunlight", cls: "sun" },
  { key: "earth_visible", label: "Earth visible", cls: "earth" },
  { key: "power_and_comms", label: "Power + comms", cls: "both" },
] as const;

export function WindowBars({ windows, windowHours, sliderHours, metrics, onSeek }: Props) {
  const pct = metrics ? [metrics.sunlight_pct, metrics.earth_visibility_pct, metrics.power_and_comms_pct] : [];
  const seek = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!onSeek) return;
    const r = e.currentTarget.getBoundingClientRect();
    onSeek(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * windowHours);
  };
  const days: number[] = [];
  for (let d = 0; d * 24 <= windowHours; d += 7) days.push(d);
  return (
    <div>
      <div className="bars">
        <div className="bars-labels">
          {ROWS.map((r) => (
            <div key={r.key}>{r.label}</div>
          ))}
        </div>
        <div
          className="bars-tracks"
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            seek(e);
          }}
          onPointerMove={(e) => e.buttons === 1 && seek(e)}
        >
          {ROWS.map((r) => (
            <div className="bar" key={r.key}>
              {barSegments(windows[r.key], windowHours).map((s, i) => (
                <div
                  key={i}
                  title={s.duration_text}
                  className={`seg-bar ${r.cls}${s.open_start ? " open-start" : ""}${s.open_end ? " open-end" : ""}`}
                  style={{ left: `${s.left * 100}%`, width: `${s.width * 100}%` }}
                />
              ))}
            </div>
          ))}
          <div className="cursor" style={{ left: `${Math.min(1, sliderHours / windowHours) * 100}%` }} />
        </div>
        <div className="bars-pct">
          {ROWS.map((r, i) => (
            <div key={r.key}>{pct[i] === undefined ? "" : formatValue(pct[i], "%", 0)}</div>
          ))}
        </div>
      </div>
      <div className="bars" style={{ marginTop: 0 }}>
        <div className="bars-labels" aria-hidden="true">
          <div style={{ height: 0 }} />
        </div>
        <div className="axis">
          {days.map((d) => (
            <span key={d} style={{ left: `${((d * 24) / windowHours) * 100}%` }}>
              day {d}
            </span>
          ))}
        </div>
        <div />
      </div>
    </div>
  );
}
EOF

put src/components/ExternalLinks.tsx '' <<'EOF'
import { useState } from "react";
import type { Site } from "../api/types";

export function ExternalLinks({ site }: { site: Site }) {
  const [copied, setCopied] = useState(false);
  const coords = `${site.lat_deg.toFixed(4)}, ${site.lon_deg.toFixed(4)}`;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(coords);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard can be blocked: the coordinates are shown as text anyway */
    }
  };
  return (
    <div className="stack">
      <p className="hint">Look at the real site: copy the coordinates, then search them in QuickMap or Moon Trek.</p>
      <div className="row">
        <span className="mono">{coords}</span>
        <button className="btn small" onClick={() => void copy()}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="row">
        <a href="https://quickmap.lroc.im-ldi.com/" target="_blank" rel="noreferrer">
          LROC QuickMap
        </a>
        <a href="https://trek.nasa.gov/moon/" target="_blank" rel="noreferrer">
          NASA Moon Trek
        </a>
      </div>
    </div>
  );
}
EOF

# ---------- screens ----------
put src/screens/ScenarioBuilder.tsx '' <<'EOF'
import { useState } from "react";
import { useSites } from "../api/queries";
import type { SiteInput } from "../api/types";
import { LatLonInput, type LatLonValue } from "../components/LatLonInput";
import type { Screen } from "../components/AppShell";
import { ScenarioCard } from "../components/ScenarioCard";
import { SitePicker } from "../components/SitePicker";
import { MAX_CARDS, MIN_CARDS } from "../lib/constants";
import { parseLatLon } from "../lib/site";
import { utcFromParts } from "../lib/time";
import { useScenarioStore } from "../state/scenarioStore";

const DEFAULT_DATE = "2027-01-10"; // the date the saved example runs were made for
const DEMO_SITES = ["connecting-ridge", "malapert-massif", "im-1", "apollo-11"]; // README 8

export function ScenarioBuilder({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const cards = useScenarioStore((s) => s.cards);
  const activeId = useScenarioStore((s) => s.activeCardId);
  const addCard = useScenarioStore((s) => s.addCard);
  const removeCard = useScenarioStore((s) => s.removeCard);
  const updateCard = useScenarioStore((s) => s.updateCard);
  const setActiveCard = useScenarioStore((s) => s.setActiveCard);
  const catalog = useSites().data?.sites;

  const [mode, setMode] = useState<"catalog" | "custom">("catalog");
  const [siteId, setSiteId] = useState<string | null>(null);
  const [custom, setCustom] = useState<LatLonValue>({ lat: "", lon: "", name: "" });
  const [date, setDate] = useState(DEFAULT_DATE);
  const [duration, setDuration] = useState("lunar");
  const [message, setMessage] = useState<string | null>(null);

  const parsed = parseLatLon(custom.lat, custom.lon);
  const dateOk = /^\d{4}-\d{2}-\d{2}$/.test(date) && date >= "1950-01-01" && date <= "2099-12-31";
  let site: SiteInput | null = null;
  if (mode === "catalog" && siteId) site = siteId;
  if (mode === "custom" && parsed.ok) site = { lat_deg: parsed.lat, lon_deg: parsed.lon, ...(custom.name.trim() ? { name: custom.name.trim() } : {}) };
  const full = cards.length >= MAX_CARDS;

  const add = () => {
    if (!site || !dateOk) return;
    const id = addCard({ site, startUtc: utcFromParts(date), windowDays: duration === "lunar" ? undefined : Number(duration) });
    setMessage(id ? null : `You can have at most ${MAX_CARDS} scenarios. Remove one to add another.`);
  };

  const addDemo = () => {
    const ids = DEMO_SITES.filter((id) => catalog?.some((s) => s.id === id));
    for (const id of ids) addCard({ site: id, startUtc: utcFromParts(DEFAULT_DATE) });
  };

  return (
    <>
      <div className="page-head">
        <h1>Build your scenarios</h1>
        <p>Each card is one site on one landing date. Add 2 to {MAX_CARDS} cards to compare them.</p>
      </div>
      <div className="cols">
        <section className="panel stack" aria-labelledby="add-h">
          <h2 id="add-h">Add a scenario</h2>
          <div className="seg" role="group" aria-label="Site source">
            <button aria-pressed={mode === "catalog"} onClick={() => setMode("catalog")}>
              Site catalog
            </button>
            <button aria-pressed={mode === "custom"} onClick={() => setMode("custom")}>
              Type coordinates
            </button>
          </div>
          {mode === "catalog" ? <SitePicker value={siteId} onChange={setSiteId} /> : <LatLonInput value={custom} onChange={setCustom} />}
          <div className="cols" style={{ gap: 12 }}>
            <label className="field">
              <span>Landing date (UTC)</span>
              <input id="landing-date" type="date" min="1950-01-01" max="2099-12-31" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label className="field">
              <span>Mission duration</span>
              <select id="duration" value={duration} onChange={(e) => setDuration(e.target.value)}>
                <option value="lunar">One lunar day (29.5 days)</option>
                <option value="14">14 days</option>
                <option value="7">7 days</option>
              </select>
            </label>
          </div>
          {!dateOk && <p className="hint bad">Pick a date between 1950 and 2099.</p>}
          {message && <p className="hint bad">{message}</p>}
          <div className="row">
            <button className="btn primary" disabled={!site || !dateOk || full} onClick={add}>
              Add scenario
            </button>
            <button className="btn" disabled={cards.length > 0 || !catalog} onClick={addDemo} title="Connecting Ridge, Malapert Massif, IM-1, Apollo 11 on 2027-01-10">
              Add the 4-site demo set
            </button>
          </div>
        </section>

        <section className="panel stack" aria-labelledby="cards-h">
          <h2 id="cards-h">Your scenarios ({cards.length}/{MAX_CARDS})</h2>
          {cards.length === 0 && <p className="hint">Nothing yet. Pick a site and a date on the left, or add the demo set.</p>}
          <div className="cards">
            {cards.map((c) => (
              <ScenarioCard
                key={c.id}
                card={c}
                catalog={catalog}
                active={c.id === activeId}
                onOpen={() => {
                  setActiveCard(c.id);
                  onNavigate("site");
                }}
                onRemove={() => removeCard(c.id)}
                onDate={(utc) => updateCard(c.id, { startUtc: utc })}
              />
            ))}
          </div>
          {cards.length > 0 && cards.length < MIN_CARDS && <p className="hint">Add at least {MIN_CARDS} scenarios to compare them.</p>}
        </section>
      </div>
    </>
  );
}
EOF

put src/screens/SiteView.tsx '' <<'EOF'
import { useSites } from "../api/queries";
import type { Screen } from "../components/AppShell";
import { Countdown } from "../components/Countdown";
import { ErrorState } from "../components/ErrorState";
import { ExternalLinks } from "../components/ExternalLinks";
import { HorizonView } from "../components/HorizonView";
import { Loading } from "../components/Loading";
import { PowerReadout } from "../components/PowerReadout";
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
        </div>
      </div>
      <WarningList warnings={data.warnings} />
      <div className="cols-sky">
        <section className="panel stack" aria-labelledby="sky-h">
          <h2 id="sky-h">Sun and Earth over the horizon, at landing</h2>
          <HorizonView profile={v.profile} sun={v.sun} earth={v.earth} sunTrail={v.sunTrail} earthTrail={v.earthTrail} />
          {timeline.isError ? (
            <p className="hint warn">Terrain skyline unavailable: {(timeline.error as Error).message}</p>
          ) : (
            <p className="hint">Faint dots show where the Sun and Earth move during the whole window. Open the Timeline to play it.</p>
          )}
          <div>
            <button className="btn primary" onClick={() => onNavigate("timeline")}>
              Open the timeline
            </button>
          </div>
        </section>
        <div className="stack">
          <Countdown body="sun" countdown={data.countdown.sun} nextEvents={data.next_events} sliderHours={0} up={v.sun?.up} />
          <Countdown body="earth" countdown={data.countdown.earth} nextEvents={data.next_events} sliderHours={0} up={v.earth?.up} />
          <section className="panel">
            <h2>Power at landing</h2>
            <PowerReadout now={data.now} sky={null} />
          </section>
        </div>
      </div>
      <div className="cols">
        <section className="panel">
          <h2>See the real site</h2>
          <ExternalLinks site={data.site} />
        </section>
        <section className="panel">
          <h2>Method and limits</h2>
          <details>
            <summary>How these numbers are made</summary>
            <ul>
              <li>Ephemeris: {data.data_sources.ephemeris_source}</li>
              {data.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </details>
        </section>
      </div>
    </>
  );
}
EOF

put src/screens/Timeline.tsx '' <<'EOF'
import { useEffect, useState } from "react";
import type { Screen } from "../components/AppShell";
import { Countdown } from "../components/Countdown";
import { ErrorState } from "../components/ErrorState";
import { HorizonView } from "../components/HorizonView";
import { Loading } from "../components/Loading";
import { PowerReadout } from "../components/PowerReadout";
import { WarningList } from "../components/WarningList";
import { WindowBars } from "../components/WindowBars";
import { WINDOW_HOURS } from "../lib/constants";
import { formatUtc } from "../lib/utc";
import { useScenarioStore } from "../state/scenarioStore";
import { skyView, useActive } from "../state/useActive";

const STEP_H = 6; // hours per tick while playing
const TICK_MS = 90; // a full lunar day plays in about 11 seconds

export function Timeline({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const { card, conditions, timeline } = useActive();
  const sliderHours = useScenarioStore((s) => s.sliderHours);
  const setSlider = useScenarioStore((s) => s.setSliderHours);
  const [playing, setPlaying] = useState(false);

  const data = timeline.data ?? conditions.data;
  const max = Math.round(data?.window.duration_h ?? WINDOW_HOURS);

  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => {
      const next = useScenarioStore.getState().sliderHours + STEP_H;
      if (next >= max) {
        setSlider(max);
        setPlaying(false);
      } else setSlider(next);
    }, TICK_MS);
    return () => window.clearInterval(id);
  }, [playing, max, setSlider]);

  if (!card) {
    return (
      <section className="panel empty">
        <h1>No scenario selected</h1>
        <p className="muted">Add a scenario first, then open its timeline.</p>
        <button className="btn primary" onClick={() => onNavigate("builder")}>
          Go to Scenarios
        </button>
      </section>
    );
  }
  if (timeline.isError) {
    return (
      <>
        <ErrorState error={timeline.error} onRetry={() => void timeline.refetch()} />
        <p className="hint">The timeline needs a timeline result for this site. In fixture mode only Connecting Ridge has one.</p>
      </>
    );
  }
  if (!timeline.data || !data) return <Loading label="Calculating the lunar day..." />;

  const tl = timeline.data;
  const h = Math.min(sliderHours, max);
  const v = skyView(conditions.data, tl, h);
  const nowText = v.sky ? formatUtc(v.sky.t_utc) : formatUtc(card.startUtc);

  return (
    <>
      <div className="page-head">
        <h1>{tl.site.name}: one lunar day</h1>
        <p>Drag the slider or press Play. The Sun and Earth move on the horizon, and the bars show when you have sunlight, a line of sight to Earth, and both.</p>
      </div>
      <WarningList warnings={tl.warnings} />
      <div className="cols-sky">
        <section className="panel stack" aria-labelledby="tl-sky">
          <h2 id="tl-sky">Horizon</h2>
          <HorizonView profile={v.profile} sun={v.sun} earth={v.earth} sunTrail={v.sunTrail} earthTrail={v.earthTrail} />
          <div className="row" style={{ justifyContent: "space-between" }}>
            <button className="btn primary" onClick={() => (h >= max ? (setSlider(0), setPlaying(true)) : setPlaying(!playing))}>
              {playing ? "Pause" : "Play"}
            </button>
            <div className="simtime" aria-live="off">
              {nowText} · day {(h / 24).toFixed(1)}
            </div>
          </div>
          <input
            id="timeline-slider"
            type="range"
            min={0}
            max={max}
            step={1}
            value={h}
            aria-label="Time since landing, in hours"
            onChange={(e) => {
              setPlaying(false);
              setSlider(Number(e.target.value));
            }}
          />
        </section>
        <div className="stack">
          <Countdown body="sun" countdown={tl.countdown.sun} nextEvents={tl.next_events} sliderHours={h} up={v.sun?.up} />
          <Countdown body="earth" countdown={tl.countdown.earth} nextEvents={tl.next_events} sliderHours={h} up={v.earth?.up} />
          <section className="panel">
            <h2>Power now</h2>
            <PowerReadout now={tl.now} sky={v.sky} />
          </section>
        </div>
      </div>
      <section className="panel stack" aria-labelledby="bars-h">
        <h2 id="bars-h">When do we have power, comms, or both?</h2>
        <WindowBars windows={tl.windows} windowHours={max} sliderHours={h} metrics={tl.metrics} onSeek={(hh) => (setPlaying(false), setSlider(hh))} />
        <p className="hint">Click or drag on the bars to jump in time. Earth visibility is geometric line of sight only, not a radio link budget.</p>
      </section>
    </>
  );
}
EOF
# ---------- page title ----------
if [ -f index.html ] && ! grep -q '<title>LunaNav' index.html; then
  sed -i 's#<title>.*</title>#<title>LunaNav</title>#' index.html && echo "set page title to LunaNav"
fi

cat <<'EOF'

Done. Now run:
  npm run dev
Open the address it prints. With VITE_USE_FIXTURES=true (in .env) it uses the saved example runs:
  1. On "Scenarios" click "Add the 4-site demo set"
  2. Open "Connecting Ridge" -> "Open site view" -> "Open the timeline" -> Play
Before a commit: npm run build and npx vitest run.
EOF

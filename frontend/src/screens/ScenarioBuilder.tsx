import { useState } from "react";
import { addDemoScenarios } from "../lib/demo";
import { Seg } from "../components/Seg";
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
    addDemoScenarios(catalog, addCard);
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
          <Seg label="Site source" value={mode} onChange={setMode} options={[{ value: "catalog", label: "Site catalog" }, { value: "custom", label: "Type coordinates" }]} />
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

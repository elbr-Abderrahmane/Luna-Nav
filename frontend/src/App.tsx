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

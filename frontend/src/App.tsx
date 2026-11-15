import { useState } from "react";
import { AppShell, type Screen } from "./components/AppShell";
import { Providers } from "./Providers";
import { Landing } from "./components/Landing";
import { ScenarioBuilder } from "./screens/ScenarioBuilder";
import { Compare } from "./screens/Compare";
import { DateSweep } from "./screens/DateSweep";
import { SiteView } from "./screens/SiteView";
import { Timeline } from "./screens/Timeline";

export default function App() {
  const [screen, setScreen] = useState<Screen>("builder");
  const [started, setStarted] = useState(false);
  if (!started) return <Landing onStart={() => setStarted(true)} />;
  return (
    <Providers>
      <AppShell screen={screen} onNavigate={setScreen}>
        {screen === "builder" && <ScenarioBuilder onNavigate={setScreen} />}
        {screen === "site" && <SiteView onNavigate={setScreen} />}
        {screen === "timeline" && <Timeline onNavigate={setScreen} />}
        {screen === "compare" && <Compare onNavigate={setScreen} />}
        {screen === "sweep" && <DateSweep onNavigate={setScreen} />}
      </AppShell>
    </Providers>
  );
}

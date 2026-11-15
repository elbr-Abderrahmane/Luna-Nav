import { useEffect, useRef, useState } from "react";
import "../landing.css";
import { LunaLogo } from "./LunaLogo";
import { Starfield } from "./Starfield";

/** First screen: title and one button. Fades out, then hands over to the app. */
export function Landing({ onStart }: { onStart: () => void }) {
  const [leaving, setLeaving] = useState(false);
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    button.current?.focus();
  }, []);

  const start = () => {
    if (leaving) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      onStart();
      return;
    }
    setLeaving(true);
    window.setTimeout(onStart, 450);
  };

  return (
    <div className={`landing${leaving ? " landing-leaving" : ""}`}>
      <Starfield />
      <main className="landing-center">
        <LunaLogo size={96} />
        <h1 className="landing-title">LUNANAV</h1>
        <button ref={button} className="landing-button" onClick={start}>
          Get started
        </button>
      </main>
    </div>
  );
}

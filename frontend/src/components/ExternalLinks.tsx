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

import { useState } from "react";
import type { Site } from "../api/types";

const MOON_RADIUS_M = 1737400.0;
const HALF_WINDOW_M = 20000.0; // ±20 km zoom box around landing site

function computePolarStereoMeters(latDeg: number, lonDeg: number, northPole = false): { x: number; y: number } {
  const latRad = (latDeg * Math.PI) / 180.0;
  const lonRad = (lonDeg * Math.PI) / 180.0;
  if (northPole) {
    const r = 2.0 * MOON_RADIUS_M * Math.tan((Math.PI / 2.0 - latRad) / 2.0);
    return {
      x: r * Math.sin(lonRad),
      y: -r * Math.cos(lonRad),
    };
  }
  const r = 2.0 * MOON_RADIUS_M * Math.tan((Math.PI / 2.0 + latRad) / 2.0);
  return {
    x: r * Math.sin(lonRad),
    y: r * Math.cos(lonRad),
  };
}

function buildQuickMap2DUrl(site: Site): string {
  const { lat_deg: lat, lon_deg: lon } = site;
  const featureParam = `${lon.toFixed(5)},${lat.toFixed(5)}`;

  if (lat <= -60.0) {
    // proj=27 is LROC QuickMap's Stereographic (South Pole) [IAU2000:30120]
    const { x, y } = computePolarStereoMeters(lat, lon, false);
    const prjExtent = [
      (x - HALF_WINDOW_M).toFixed(1),
      (y - HALF_WINDOW_M).toFixed(1),
      (x + HALF_WINDOW_M).toFixed(1),
      (y + HALF_WINDOW_M).toFixed(1),
    ].join(",");
    return `https://quickmap.lroc.im-ldi.com/?proj=27&prjExtent=${prjExtent}&features=${featureParam}`;
  }

  if (lat >= 60.0) {
    // proj=26 is LROC QuickMap's Stereographic (North Pole) [IAU2000:30118]
    const { x, y } = computePolarStereoMeters(lat, lon, true);
    const prjExtent = [
      (x - HALF_WINDOW_M).toFixed(1),
      (y - HALF_WINDOW_M).toFixed(1),
      (x + HALF_WINDOW_M).toFixed(1),
      (y + HALF_WINDOW_M).toFixed(1),
    ].join(",");
    return `https://quickmap.lroc.im-ldi.com/?proj=26&prjExtent=${prjExtent}&features=${featureParam}`;
  }

  // proj=16 is Equidistant Cylindrical (< 75 deg.) [IAU2000:30110]
  const x = MOON_RADIUS_M * ((lon * Math.PI) / 180.0);
  const y = MOON_RADIUS_M * ((lat * Math.PI) / 180.0);
  const prjExtent = [
    (x - HALF_WINDOW_M).toFixed(1),
    (y - HALF_WINDOW_M).toFixed(1),
    (x + HALF_WINDOW_M).toFixed(1),
    (y + HALF_WINDOW_M).toFixed(1),
  ].join(",");
  return `https://quickmap.lroc.im-ldi.com/?proj=16&prjExtent=${prjExtent}&features=${featureParam}`;
}

function buildQuickMap3DUrl(site: Site): string {
  const { lat_deg: lat, lon_deg: lon } = site;
  const featureParam = `${lon.toFixed(5)},${lat.toFixed(5)}`;
  // proj=22 is LROC QuickMap's 3D Lunar Globe
  const d = 0.8;
  const extent = [
    (lon - d).toFixed(4),
    Math.max(-90, lat - d).toFixed(4),
    (lon + d).toFixed(4),
    Math.min(90, lat + d).toFixed(4),
  ].join(",");
  return `https://quickmap.lroc.im-ldi.com/?proj=22&extent=${extent}&features=${featureParam}`;
}

export function ExternalLinks({ site }: { site: Site }) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const isSouthPolar = site.lat_deg <= -60.0;
  const isNorthPolar = site.lat_deg >= 60.0;
  const isPolar = isSouthPolar || isNorthPolar;

  const coords180 = `${site.lat_deg.toFixed(4)}, ${site.lon_deg.toFixed(4)}`;
  const lon360 = ((site.lon_deg % 360) + 360) % 360;
  const coords360 = `${site.lat_deg.toFixed(4)}, ${lon360.toFixed(4)}`;
  const stereo = isPolar ? computePolarStereoMeters(site.lat_deg, site.lon_deg, isNorthPolar) : null;
  const coordsStereo = stereo ? `${Math.round(stereo.x)}, ${Math.round(stereo.y)}` : null;

  const copyText = async (key: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 1500);
    } catch {
      /* clipboard can be blocked: the coordinates are shown as text anyway */
    }
  };

  const quickMap2DUrl = buildQuickMap2DUrl(site);
  const quickMap3DUrl = buildQuickMap3DUrl(site);

  return (
    <div className="stack">
      <p className="hint">Look at the real site: open directly in QuickMap (Polar/3D) or copy coordinates for Moon Trek.</p>
      <div className="row">
        <span className="mono">{coords180}</span>
        <button className="btn small" onClick={() => void copyText("180", coords180)}>
          {copiedKey === "180" ? "Copied" : "Copy"}
        </button>
      </div>
      <div className="row">
        <a href={quickMap2DUrl} target="_blank" rel="noreferrer">
          {isSouthPolar
            ? "LROC QuickMap (South Pole)"
            : isNorthPolar
              ? "LROC QuickMap (North Pole)"
              : "LROC QuickMap"}
        </a>
        <a href={quickMap3DUrl} target="_blank" rel="noreferrer">
          QuickMap 3D Globe
        </a>
        <a href="https://trek.nasa.gov/moon/" target="_blank" rel="noreferrer">
          NASA Moon Trek
        </a>
      </div>
      <details className="pop">
        <summary>Projection &amp; Coordinate Formats</summary>
        <div className="pop-body">
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>
                Lat, Lon (±180°): <span className="mono">{coords180}</span>
              </span>
              <button className="btn small" onClick={() => void copyText("180", coords180)}>
                {copiedKey === "180" ? "Copied" : "Copy"}
              </button>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>
                Lat, Lon (0–360°E): <span className="mono">{coords360}</span>
              </span>
              <button className="btn small" onClick={() => void copyText("360", coords360)}>
                {copiedKey === "360" ? "Copied" : "Copy 360°E"}
              </button>
            </div>
            {coordsStereo && (
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span>
                  Polar Stereo X, Y (m): <span className="mono">{coordsStereo}</span>
                </span>
                <button className="btn small" onClick={() => void copyText("stereo", coordsStereo)}>
                  {copiedKey === "stereo" ? "Copied" : "Copy X,Y (m)"}
                </button>
              </div>
            )}
            {isPolar && (
              <p style={{ margin: "0.25rem 0 0", fontSize: "0.82rem", lineHeight: 1.4, opacity: 0.9 }}>
                <strong>Polar projection note:</strong> QuickMap and Moon Trek default to <em>Equatorial Cylindrical</em>{" "}
                projection (±60°–75°). Our <strong>LROC QuickMap ({isSouthPolar ? "South Pole" : "North Pole"})</strong>{" "}
                link automatically switches to <span className="mono">{isSouthPolar ? "proj=27" : "proj=26"}</span> and
                drops a marker pin. In <strong>NASA Moon Trek</strong>, switch the bottom-left <em>Projections</em> menu
                to <strong>{isSouthPolar ? "South Polar Stereographic" : "North Polar Stereographic"}</strong> (or{" "}
                <strong>3D Globe</strong>) before searching <span className="mono">{coords180}</span>.
              </p>
            )}
          </div>
        </div>
      </details>
    </div>
  );
}

import { useEffect, useRef } from "react";
import { useTerrainHeightmap } from "../api/queries";
import type { Site, TerrainInfo } from "../api/types";
import { formatValue } from "../lib/format";

function elevationColor(t: number): [number, number, number] {
  const c = Math.max(0, Math.min(1, t));
  if (c < 0.25) {
    const k = c / 0.25;
    return [Math.round(20 + 22 * k), Math.round(33 + 124 * k), Math.round(61 + 82 * k)];
  }
  if (c < 0.6) {
    const k = (c - 0.25) / 0.35;
    return [Math.round(42 + 191 * k), Math.round(157 + 39 * k), Math.round(143 - 37 * k)];
  }
  if (c < 0.85) {
    const k = (c - 0.6) / 0.25;
    return [Math.round(233 + 11 * k), Math.round(196 - 34 * k), Math.round(106 - 9 * k)];
  }
  const k = (c - 0.85) / 0.15;
  return [Math.round(244 + 11 * k), Math.round(162 + 93 * k), Math.round(97 + 158 * k)];
}

export function TerrainCard({ site, terrain }: { site: Site; terrain?: TerrainInfo }) {
  const isPolar = site.lat_deg <= -80;
  const hmQuery = useTerrainHeightmap(site.lat_deg, site.lon_deg, 1600);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const hm = hmQuery.data;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !hm || hm.status !== "ok" || !hm.elevations_m.length) return;
    const rows = hm.elevations_m.length;
    const cols = hm.elevations_m[0]?.length ?? 0;
    if (!rows || !cols) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const minE = hm.min_elevation_m ?? 0;
    const maxE = hm.max_elevation_m ?? minE + 1;
    const span = Math.max(1e-3, maxE - minE);

    const w = canvas.width;
    const h = canvas.height;
    const img = ctx.createImageData(w, h);

    for (let py = 0; py < h; py++) {
      const rIdx = Math.min(rows - 1, Math.floor((py / h) * rows));
      for (let px = 0; px < w; px++) {
        const cIdx = Math.min(cols - 1, Math.floor((px / w) * cols));
        const val = hm.elevations_m[rIdx]?.[cIdx];
        const idx = (py * w + px) * 4;
        if (val === null || val === undefined) {
          img.data[idx] = 30;
          img.data[idx + 1] = 30;
          img.data[idx + 2] = 40;
          img.data[idx + 3] = 255;
        } else {
          const [cr, cg, cb] = elevationColor((val - minE) / span);
          img.data[idx] = cr;
          img.data[idx + 1] = cg;
          img.data[idx + 2] = cb;
          img.data[idx + 3] = 255;
        }
      }
    }
    ctx.putImageData(img, 0, 0);

    // Draw crosshair at center (landing site)
    const cx = Math.floor(w / 2);
    const cy = Math.floor(h / 2);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.moveTo(cx - 10, cy);
    ctx.lineTo(cx + 10, cy);
    ctx.moveTo(cx, cy - 10);
    ctx.lineTo(cx, cy + 10);
    ctx.stroke();
  }, [hm]);

  if (!isPolar) {
    return (
      <section className="panel stack">
        <h2>Local terrain (LOLA DEM)</h2>
        <p className="hint">
          Site latitude is {site.lat_deg.toFixed(2)}°. The south-polar LOLA DEM covers 80°S to 90°S; non-polar sites use the smooth-sphere reference horizon.
        </p>
      </section>
    );
  }

  const elev = site.elevation_m ?? terrain?.summary?.mean_elevation_m ?? null;
  const slope = terrain?.slope_deg ?? null;
  const roughness = terrain?.roughness_m ?? terrain?.summary?.roughness_m ?? null;
  const minE = hm?.min_elevation_m ?? terrain?.summary?.min_elevation_m ?? null;
  const maxE = hm?.max_elevation_m ?? terrain?.summary?.max_elevation_m ?? null;

  return (
    <section className="panel stack">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h2>Local terrain (LOLA 80–90°S DEM)</h2>
        <span className={`badge ${terrain?.coverage?.pixel_covered ? "ok" : "warn"}`}>
          {terrain?.coverage?.pixel_covered ? "DEM covered" : "No local DEM"}
        </span>
      </div>
      <div className="row" style={{ gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
        {hm && hm.status === "ok" && hm.elevations_m.length > 0 && (
          <div className="stack" style={{ gap: 4, alignItems: "center" }}>
            <canvas
              ref={canvasRef}
              width={160}
              height={160}
              aria-label="Local 3.2 km LOLA elevation heightmap around landing site"
              style={{ borderRadius: 6, border: "1px solid rgba(255,255,255,0.15)" }}
            />
            <span className="muted small">3.2 × 3.2 km window (crosshair = landing site)</span>
          </div>
        )}
        <dl className="stats" style={{ flex: 1, minWidth: 180 }}>
          <div>
            <dt>Elevation (ref 1737.4 km)</dt>
            <dd>{elev !== null && elev !== undefined ? formatValue(elev, "m", 0) : "—"}</dd>
          </div>
          <div>
            <dt>Local slope (3×3 Horn)</dt>
            <dd>{slope !== null && slope !== undefined ? formatValue(slope, "°", 1) : "—"}</dd>
          </div>
          <div>
            <dt>Surface roughness (RMS)</dt>
            <dd>{roughness !== null && roughness !== undefined ? formatValue(roughness, "m", 1) : "—"}</dd>
          </div>
          <div>
            <dt>Local window min / max</dt>
            <dd>
              {minE !== null && maxE !== null
                ? `${Math.round(minE)} m .. ${Math.round(maxE)} m`
                : "—"}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

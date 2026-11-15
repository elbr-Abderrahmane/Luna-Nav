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

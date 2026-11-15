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

import type { CompareKey } from "../api/types";

export const METRICS: { key: CompareKey; label: string; unit: string; digits: number }[] = [
  { key: "power_and_comms_pct", label: "Power + comms", unit: "%", digits: 0 },
  { key: "sunlight_pct", label: "Sunlight", unit: "%", digits: 0 },
  { key: "earth_visibility_pct", label: "Earth visible", unit: "%", digits: 0 },
  { key: "longest_darkness_h", label: "Longest night", unit: "h", digits: 0 },
  { key: "longest_comms_gap_h", label: "Longest comms gap", unit: "h", digits: 0 },
  { key: "vertical_panel_energy_kwh_m2", label: "Vertical panel energy", unit: "kWh/m2", digits: 0 },
  { key: "sun_elevation_deg_max", label: "Max Sun elevation", unit: "deg", digits: 1 },
];

export const VERDICT_TEXT = { viable: "Viable", marginal: "Marginal", not_viable: "Not viable" } as const;

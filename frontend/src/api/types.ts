// Typed by hand from README section 6. mock_data/astro/*.json (real P3 runs) win over this file:
// when you open a fixture and a field differs, fix it here.
// Note: README's `Window` is named `TimeWindow` here to avoid clashing with the DOM `Window`.

export type UTC = string; // "2027-01-10T00:00:00Z"

export interface Envelope {
  status: "ok" | "error";
  result_type: "ephemeris_calculation";
  warnings: string[]; // show on the card
  data_sources: { ephemeris_backend: string; ephemeris_source: string };
  limitations: string[];
}

export interface ErrorBody {
  error: { code: string; message: string }; // UNKNOWN_SITE, INVALID_COORDINATES, INVALID_WINDOW, INVALID_SCENARIOS...
}

export type SiteInput = string | { lat_deg: number; lon_deg: number; name?: string; elevation_m?: number };

export type SiteCategory = "apollo" | "artemis" | "clps" | "international" | "south_pole_candidate" | "reference" | "custom";

export interface Site {
  id: string | null;
  name: string;
  category: SiteCategory;
  mission: string | null;
  agency: string | null;
  coord_quality: "landed" | "approximate" | "exact" | "user_input";
  lat_deg: number;
  lon_deg: number;
  /** Missing in the sites.json catalog; present in the Site returned with conditions. */
  elevation_m?: number;
  /** Catalog only: reference | candidate | landed | planned ... (checked against mock_data/astro/sites.json) */
  status?: string;
  notes?: string | null;
}

export interface SitesResponse {
  status: "ok" | "error";
  sites: Site[];
}

export interface BodyNow {
  azimuth_deg: number;
  elevation_deg: number;
  horizon_elevation_deg: number;
  margin_above_horizon_deg: number; // elevation - horizon; > 0 = up
  visible: boolean;
  disk_visible_fraction: number; // 0..1
  apparent_radius_deg: number;
  distance_km: number;
}

export interface Countdown {
  next_event: "sunset" | "sunrise" | "earthset" | "earthrise";
  next_event_utc: UTC | null;
  time_remaining_h: number | null;
  time_remaining_text: string | null;
  beyond_window: boolean; // true = no change during the whole window
  summary: string; // "Earthrise in 21 h 37 min" / "Sun stays up for the whole 29.5-day window"
}

export interface NextEvent {
  event: string; // sunset | sunrise | earthset | earthrise
  t_utc: UTC;
  in_h: number;
  in_text: string;
}

export interface TimeWindow {
  start_utc: UTC;
  end_utc: UTC;
  duration_h: number;
  duration_text: string;
  starts_in_h: number;
  open_at_window_start: boolean;
  open_at_window_end: boolean;
}

export interface Windows {
  sunlit: TimeWindow[];
  earth_visible: TimeWindow[];
  power_and_comms: TimeWindow[];
}

export interface Metrics {
  sunlight_pct: number;
  sunlight_hours: number;
  longest_darkness_h: number;
  earth_visibility_pct: number;
  earth_visible_hours: number;
  longest_comms_gap_h: number;
  power_and_comms_pct: number;
  sun_elevation_deg_max: number;
  sun_elevation_deg_min: number;
  sun_elevation_deg_mean_when_lit: number | null;
  earth_elevation_deg_max: number;
  earth_elevation_deg_min: number;
  mean_vertical_panel_factor: number;
  mean_horizontal_panel_factor: number;
  vertical_panel_energy_kwh_m2: number;
  n_sunsets: number;
  n_earthsets: number;
  libration_lat_range_deg: [number, number];
  libration_lon_range_deg: [number, number];
}

export interface TerrainInfo {
  coverage?: {
    status: string;
    nominal_coverage: boolean;
    raster_coverage: boolean;
    pixel_covered: boolean;
    elevation_m: number | null;
  };
  slope_deg?: number | null;
  slope_status?: string;
  roughness_m?: number | null;
}

export interface SiteConditions extends Envelope {
  site: Site;
  method: "horizon_mask" | "smooth_sphere";
  window: {
    start_utc: UTC;
    end_utc: UTC;
    duration_h: number;
    duration_days: number;
    sampling_interval_h: number;
    n_samples: number;
  };
  now: {
    t_utc: UTC;
    sun: BodyNow;
    earth: BodyNow;
    power: {
      irradiance_w_m2: number;
      vertical_panel_factor: number;
      horizontal_panel_factor: number;
      vertical_panel_w_m2: number;
    };
    libration: { sub_earth_lat_deg: number; sub_earth_lon_deg: number };
    sub_solar: { lat_deg: number; lon_deg: number };
  };
  countdown: { sun: Countdown; earth: Countdown };
  next_events: NextEvent[];
  windows: Windows;
  metrics: Metrics;
  verdict?: Verdict;
  verdict_explanation?: string;
  terrain?: TerrainInfo;
}

export interface TimelineSeries {
  t_utc: UTC[];
  hours_from_start: number[];
  sun_azimuth_deg: number[];
  sun_elevation_deg: number[];
  sun_horizon_deg: number[];
  sun_disk_visible_fraction: number[];
  earth_azimuth_deg: number[];
  earth_elevation_deg: number[];
  earth_horizon_deg: number[];
  earth_visible: boolean[];
  irradiance_w_m2: number[];
}

export interface SiteTimeline extends SiteConditions {
  series: TimelineSeries;
  /** 360 azimuth bins: draw this as the skyline. */
  horizon_profile: { azimuth_deg: number[]; elevation_deg: number[]; method: string };
}

export type CompareKey =
  | "sunlight_pct"
  | "longest_darkness_h"
  | "earth_visibility_pct"
  | "longest_comms_gap_h"
  | "power_and_comms_pct"
  | "vertical_panel_energy_kwh_m2"
  | "sun_elevation_deg_max";

export interface Verdict {
  level: "viable" | "marginal" | "not_viable";
  reasons: string[];
  summary: string;
  thresholds: Record<string, number>;
}

export interface CompareRow {
  label: string;
  site: Site;
  start_utc: UTC;
  method: string;
  warnings: string[];
  sunlit_at_start: boolean;
  sun_elevation_deg_at_start: number;
  earth_visible_at_start: boolean;
  earth_elevation_deg_at_start: number;
  sun_countdown: Countdown;
  earth_countdown: Countdown;
  metrics: Metrics;
  windows: Windows;
  verdict: Verdict; // added by P5 from P4's rule (not in the P3 output)
}

export interface BestOf {
  label: string;
  value: number;
  direction: "higher_is_better" | "lower_is_better";
}

export interface RankingEntry {
  label: string;
  verdict_level?: "viable" | "marginal" | "not_viable" | null;
  normalized: Record<string, number>;
  wsm_score?: number;
  wsm_rank?: number;
  topsis_score?: number;
  topsis_rank?: number;
}

export interface RankingResult {
  method: "wsm" | "topsis" | "both";
  profile: "engineering" | "science" | "custom";
  weights: Record<string, number>;
  ranking: RankingEntry[];
  note?: string;
}

export interface SensitivityResult {
  base_top: string;
  stability: "stable" | "moderate" | "sensitive";
  top_never_changes: boolean;
  random_weights: {
    n: number;
    seed: number;
    top_win_share_pct: Record<string, number>;
  };
  profile_comparison: {
    science_top: string;
    engineering_top: string;
    agree: boolean;
  };
}

export interface Compare extends Envelope {
  n_scenarios: number;
  rows: CompareRow[];
  best: Record<CompareKey, BestOf>;
  explanation?: string;
  ranking?: RankingResult;
  sensitivity?: SensitivityResult;
  ranking_explanation?: string;
}

export type DateSweepRow = Omit<CompareRow, "windows" | "verdict"> & {
  sub_solar_lat_deg: number;
  verdict?: Verdict;
};

export interface DateSweep extends Envelope {
  site: Site;
  every_days: number;
  window_days: number;
  rows: DateSweepRow[]; // label = "YYYY-MM-DD"
  best: Record<CompareKey, BestOf>;
  explanation?: string;
}

// ---- request bodies ----
export interface ConditionsRequest { site: SiteInput; start_utc: UTC; window_days?: number }
export interface TimelineRequest { site: SiteInput; start_utc: UTC; days?: number; step_h?: number }
export interface CompareRequest {
  scenarios: { site: SiteInput; start_utc: UTC; label?: string; window_days?: number }[];
}
export interface DateSweepRequest { site: SiteInput; first_start_utc: UTC; n?: number; every_days?: number }

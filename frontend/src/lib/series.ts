import type { SiteTimeline } from "../api/types";

/** Index of the sample closest to `hours` (arrays are sorted ascending). Clamped to the ends. */
export function indexAtHours(hoursFromStart: number[], hours: number): number {
  if (hoursFromStart.length === 0) return -1;
  let lo = 0;
  let hi = hoursFromStart.length - 1;
  if (hours <= hoursFromStart[lo]) return lo;
  if (hours >= hoursFromStart[hi]) return hi;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (hoursFromStart[mid] <= hours) lo = mid;
    else hi = mid;
  }
  return hours - hoursFromStart[lo] <= hoursFromStart[hi] - hours ? lo : hi;
}

export interface SkyBody {
  azimuth_deg: number;
  elevation_deg: number;
  horizon_deg: number;
  /** elevation - horizon, for drawing only. > 0 means the centre of the disk is above the horizon. */
  margin_deg: number;
}

export interface SkyAtSlider {
  t_utc: string;
  hours_from_start: number;
  sun: SkyBody & { disk_visible_fraction: number };
  earth: SkyBody & { visible: boolean };
  irradiance_w_m2: number;
}

/** Where the Sun and Earth are for the slider position: reads the nearest sample of the timeline. */
export function skyAtHours(tl: Pick<SiteTimeline, "series">, hours: number): SkyAtSlider | null {
  const s = tl.series;
  const i = indexAtHours(s.hours_from_start, hours);
  if (i < 0) return null;
  return {
    t_utc: s.t_utc[i],
    hours_from_start: s.hours_from_start[i],
    sun: {
      azimuth_deg: s.sun_azimuth_deg[i],
      elevation_deg: s.sun_elevation_deg[i],
      horizon_deg: s.sun_horizon_deg[i],
      margin_deg: s.sun_elevation_deg[i] - s.sun_horizon_deg[i],
      disk_visible_fraction: s.sun_disk_visible_fraction[i],
    },
    earth: {
      azimuth_deg: s.earth_azimuth_deg[i],
      elevation_deg: s.earth_elevation_deg[i],
      horizon_deg: s.earth_horizon_deg[i],
      margin_deg: s.earth_elevation_deg[i] - s.earth_horizon_deg[i],
      visible: s.earth_visible[i],
    },
    irradiance_w_m2: s.irradiance_w_m2[i],
  };
}

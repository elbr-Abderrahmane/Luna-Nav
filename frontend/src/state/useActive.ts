import { useConditions, useTimeline } from "../api/queries";
import type { SiteConditions, SiteTimeline } from "../api/types";
import { skyAtHours, type SkyAtSlider } from "../lib/series";
import { useScenarioStore } from "./scenarioStore";

/** The active card and its two results. Conditions are fast; the timeline adds the skyline and the paths. */
export function useActive() {
  const cards = useScenarioStore((s) => s.cards);
  const activeId = useScenarioStore((s) => s.activeCardId);
  const card = cards.find((c) => c.id === activeId) ?? null;
  const conditions = useConditions(card);
  const timeline = useTimeline(card);
  return { card, conditions, timeline };
}

export interface BodyOnSky {
  az: number;
  el: number;
  up: boolean;
}
export interface Trail {
  az: number[];
  el: number[];
}

/** What HorizonView draws for a slider position. At slider 0 it uses the landing-moment numbers. */
export function skyView(conditions: SiteConditions | undefined, timeline: SiteTimeline | undefined, sliderHours: number) {
  const sky: SkyAtSlider | null = timeline && sliderHours > 0 ? skyAtHours(timeline, sliderHours) : null;
  const now = conditions?.now ?? timeline?.now;
  let sun: BodyOnSky | null = null;
  let earth: BodyOnSky | null = null;
  if (sky) {
    sun = { az: sky.sun.azimuth_deg, el: sky.sun.elevation_deg, up: sky.sun.margin_deg > 0 };
    earth = { az: sky.earth.azimuth_deg, el: sky.earth.elevation_deg, up: sky.earth.visible };
  } else if (now) {
    sun = { az: now.sun.azimuth_deg, el: now.sun.elevation_deg, up: now.sun.visible };
    earth = { az: now.earth.azimuth_deg, el: now.earth.elevation_deg, up: now.earth.visible };
  }
  const s = timeline?.series;
  return {
    sky,
    profile: timeline?.horizon_profile ?? null,
    sun,
    earth,
    sunTrail: s ? ({ az: s.sun_azimuth_deg, el: s.sun_elevation_deg } as Trail) : null,
    earthTrail: s ? ({ az: s.earth_azimuth_deg, el: s.earth_elevation_deg } as Trail) : null,
  };
}

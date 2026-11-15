// Mirror of the UI constants in README 5.6. Astro constants live in backend astro/scenarios.py.
export const MOON_RADIUS_M = 1_737_400;
export const SYNODIC_MONTH_D = 29.530589;
/** One lunar day in hours: 708.7 h. The timeline slider goes from 0 to this. */
export const WINDOW_HOURS = SYNODIC_MONTH_D * 24;
export const MIN_CARDS = 2; // UI (the API accepts 1-12)
export const MAX_CARDS = 4;
export const SWEEP_N = 12; // API accepts 1-36
export const SWEEP_EVERY_D = SYNODIC_MONTH_D;

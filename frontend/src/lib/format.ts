export const NOT_AVAILABLE = "Not available";

/** null, undefined and NaN become "Not available" instead of a made-up number. */
export function formatValue(v: number | null | undefined, unit = "", digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NOT_AVAILABLE;
  return unit ? `${v.toFixed(digits)} ${unit}` : v.toFixed(digits);
}

/**
 * Only for values the frontend derives itself (for example a countdown moved by the slider).
 * Values from the API come with a ready *_text field: show that instead (README 5.1).
 * Same style as the API: "3 d 4 h 12 min", "21 h 37 min", "30 min".
 */
export function formatDuration(hours: number | null | undefined): string {
  if (hours === null || hours === undefined || Number.isNaN(hours) || hours < 0) return NOT_AVAILABLE;
  const total = Math.round(hours * 60);
  const d = Math.floor(total / 1440);
  const h = Math.floor((total % 1440) / 60);
  const m = total % 60;
  if (d > 0) return `${d} d ${h} h ${m} min`;
  if (h > 0) return `${h} h ${m} min`;
  return `${m} min`;
}

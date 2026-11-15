import type { Site, SiteInput } from "../api/types";

/** Display name for a card's site: catalog name, typed name, or the coordinates. */
export function siteLabel(site: SiteInput, catalog?: Site[]): string {
  if (typeof site === "string") return catalog?.find((s) => s.id === site)?.name ?? site;
  return site.name ?? `${site.lat_deg.toFixed(2)}, ${site.lon_deg.toFixed(2)}`;
}

export function parseLatLon(lat: string, lon: string): { ok: true; lat: number; lon: number } | { ok: false; error: string } {
  const la = Number(lat.trim());
  const lo = Number(lon.trim());
  if (lat.trim() === "" || lon.trim() === "") return { ok: false, error: "Enter a latitude and a longitude." };
  if (!Number.isFinite(la) || !Number.isFinite(lo)) return { ok: false, error: "Latitude and longitude must be numbers." };
  if (la < -90 || la > 90) return { ok: false, error: "Latitude must be between -90 and 90 (south pole = -90)." };
  if (lo < -180 || lo > 180) return { ok: false, error: "Longitude must be between -180 and 180 (east is positive)." };
  return { ok: true, lat: la, lon: lo };
}

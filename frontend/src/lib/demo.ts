import type { Site, SiteInput } from "../api/types";
import { MAX_CARDS } from "./constants";
import { utcFromParts } from "./time";

export const DEMO_DATE = "2027-01-10"; // the date the saved example runs were made for

// Preferred demo sites (README 8), matched by id or by name. If one is missing from the catalog,
// other catalog sites fill the gap so the set is always MAX_CARDS (4) different sites.
const PREFERRED: { id?: string; name?: RegExp }[] = [
  { id: "connecting-ridge", name: /connecting ridge/i },
  { id: "malapert-massif", name: /malapert massif/i },
  { id: "im-1", name: /\bIM-1\b/i },
  { id: "apollo-11", name: /apollo 11/i },
];

export function pickDemoSites(catalog: Site[], count = MAX_CARDS): string[] {
  const sites = catalog.filter((s): s is Site & { id: string } => !!s.id);
  const chosen: string[] = [];
  const take = (s: { id: string } | undefined) => {
    if (s && !chosen.includes(s.id)) chosen.push(s.id);
  };
  for (const p of PREFERRED) take(sites.find((s) => s.id === p.id) ?? (p.name ? sites.find((s) => p.name!.test(s.name)) : undefined));
  // fill with sites from categories not used yet, then with anything left
  const usedCats = new Set(chosen.map((id) => sites.find((s) => s.id === id)?.category));
  for (const s of sites) {
    if (chosen.length >= count) break;
    if (!usedCats.has(s.category)) {
      take(s);
      usedCats.add(s.category);
    }
  }
  for (const s of sites) if (chosen.length < count) take(s);
  return chosen.slice(0, count);
}

/** Adds the demo scenarios; returns how many were added. */
export function addDemoScenarios(
  catalog: Site[] | undefined,
  addCard: (c: { site: SiteInput; startUtc: string }) => string | null,
): number {
  if (!catalog) return 0;
  let added = 0;
  for (const id of pickDemoSites(catalog)) if (addCard({ site: id, startUtc: utcFromParts(DEMO_DATE) })) added++;
  return added;
}

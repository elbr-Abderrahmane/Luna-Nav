import { useQuery } from "@tanstack/react-query";
import { MIN_CARDS, SWEEP_N } from "../lib/constants";
import type { ScenarioCard } from "../state/scenarioStore";
import { apiGet, apiPost } from "./client";
import type {
  Compare, CompareRequest, ConditionsRequest, DateSweep, DateSweepRequest,
  SiteConditions, SiteInput, SiteTimeline, SitesResponse, TimelineRequest,
} from "./types";

/** Stable cache key for a site: catalog id, or rounded coordinates for a typed one. */
export const siteKey = (s: SiteInput): string => (typeof s === "string" ? s : `${s.lat_deg.toFixed(4)},${s.lon_deg.toFixed(4)}`);

// Results are cached by (site, startUtc, window) so changing one card refetches only that card (README 7).
const cardKey = (c: ScenarioCard) => [siteKey(c.site), c.startUtc, c.windowDays ?? null] as const;

export const useSites = (category?: string) =>
  useQuery({ queryKey: ["sites", category ?? null], queryFn: () => apiGet<SitesResponse>("/sites", { category }), staleTime: Infinity });

export const useConditions = (card: ScenarioCard | null) =>
  useQuery({
    queryKey: ["conditions", ...(card ? cardKey(card) : [])],
    enabled: !!card,
    queryFn: () => {
      const body: ConditionsRequest = { site: card!.site, start_utc: card!.startUtc, window_days: card!.windowDays };
      return apiPost<SiteConditions>("/scenarios/conditions", body);
    },
  });

export const useTimeline = (card: ScenarioCard | null) =>
  useQuery({
    queryKey: ["timeline", ...(card ? cardKey(card) : [])],
    enabled: !!card,
    queryFn: () => {
      const body: TimelineRequest = { site: card!.site, start_utc: card!.startUtc, days: card!.windowDays };
      return apiPost<SiteTimeline>("/scenarios/timeline", body);
    },
  });

export const useCompare = (cards: ScenarioCard[]) =>
  useQuery({
    queryKey: ["compare", ...cards.map((c) => cardKey(c).join("|") + "|" + (c.label ?? ""))],
    enabled: cards.length >= MIN_CARDS,
    queryFn: () => {
      const body: CompareRequest = {
        scenarios: cards.map((c) => ({ site: c.site, start_utc: c.startUtc, label: c.label, window_days: c.windowDays })),
      };
      return apiPost<Compare>("/scenarios/compare", body);
    },
  });

export const useDateSweep = (site: SiteInput | null, firstStartUtc: string | null, n = SWEEP_N) =>
  useQuery({
    queryKey: ["sweep", site ? siteKey(site) : null, firstStartUtc, n],
    enabled: !!site && !!firstStartUtc,
    queryFn: () => {
      const body: DateSweepRequest = { site: site!, first_start_utc: firstStartUtc!, n };
      return apiPost<DateSweep>("/scenarios/date-sweep", body);
    },
  });

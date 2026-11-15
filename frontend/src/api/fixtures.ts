// Maps an API call to a real P3 output in mock_data/astro/ (README 4 and 8). No import.meta here, so it is testable.
// Files: sites.json, site_conditions_<site-id>.json, site_timeline_<site-id>.json,
//        compare_four_sites.json, date_sweep_<site-id>.json
import type { Metrics, Verdict } from "./types";

export class FixtureMissingError extends Error {}

/** Keys contain "mock_data/astro/<file>"; values load the file as text. */
export type FixtureFiles = Record<string, () => Promise<string>>;
type Params = Record<string, string | number | undefined>;
const DIR = "mock_data/astro/";

async function load<T>(files: FixtureFiles, name: string): Promise<T> {
  const key = Object.keys(files).find((k) => k.endsWith(DIR + name));
  if (!key) throw new FixtureMissingError(`No fixture file ${DIR}${name}`);
  return JSON.parse(await files[key]()) as T;
}

function siteIdOf(body: unknown): string | null {
  const site = (body as { site?: unknown } | undefined)?.site;
  return typeof site === "string" ? site : null;
}

async function loadForSite<T>(files: FixtureFiles, prefix: string, body: unknown): Promise<T> {
  const id = siteIdOf(body);
  if (!id) throw new FixtureMissingError("Custom coordinates need the live API. Set VITE_USE_FIXTURES=false.");
  try {
    return await load<T>(files, `${prefix}_${id}.json`);
  } catch (e) {
    if (e instanceof FixtureMissingError) {
      throw new FixtureMissingError(`No ${prefix} fixture for "${id}". Fixtures cover only a few sites; use the live API for this one.`);
    }
    throw e;
  }
}

/**
 * PLACEHOLDER verdict for fixture mode only: README 6.5 says to add a fake verdict until P4's rule is in.
 * It applies the README's default thresholds. The real verdict comes from the API (P4); delete this when it does.
 */
export function placeholderVerdict(
  m: Pick<Metrics, "sunlight_pct" | "longest_darkness_h" | "earth_visibility_pct" | "longest_comms_gap_h">,
  customThresholds?: Record<string, number>,
): Verdict {
  const thresholds = {
    not_viable_longest_darkness_h_above: customThresholds?.not_viable_longest_darkness_h_above ?? 100,
    not_viable_sunlight_pct_below: customThresholds?.not_viable_sunlight_pct_below ?? Math.min(30, customThresholds?.viable_sunlight_pct_min ?? 60),
    not_viable_earth_visibility_pct_below: customThresholds?.not_viable_earth_visibility_pct_below ?? Math.min(20, customThresholds?.viable_earth_visibility_pct_min ?? 50),
    viable_sunlight_pct_min: customThresholds?.viable_sunlight_pct_min ?? 60,
    viable_longest_darkness_h_max: customThresholds?.viable_longest_darkness_h_max ?? 50,
    viable_earth_visibility_pct_min: customThresholds?.viable_earth_visibility_pct_min ?? 50,
    viable_longest_comms_gap_h_max: customThresholds?.viable_longest_comms_gap_h_max ?? 72,
  };
  const bad: string[] = [];
  if (m.longest_darkness_h > thresholds.not_viable_longest_darkness_h_above) {
    bad.push(`Longest night is ${Math.round(m.longest_darkness_h)} h, above the ${thresholds.not_viable_longest_darkness_h_above} h hard limit.`);
  }
  if (m.sunlight_pct < thresholds.not_viable_sunlight_pct_below) {
    bad.push(`Sunlight is ${Math.round(m.sunlight_pct)} %, below the ${thresholds.not_viable_sunlight_pct_below} % hard floor.`);
  }
  if (m.earth_visibility_pct < thresholds.not_viable_earth_visibility_pct_below) {
    bad.push(`Earth visibility is ${Math.round(m.earth_visibility_pct)} %, below the ${thresholds.not_viable_earth_visibility_pct_below} % hard floor.`);
  }
  const tag = "[placeholder verdict, fixture mode] ";
  if (bad.length) {
    return {
      level: "not_viable",
      reasons: bad,
      summary: tag + "Not viable: " + bad[0],
      thresholds,
    };
  }

  const short: string[] = [];
  if (m.sunlight_pct < thresholds.viable_sunlight_pct_min) {
    short.push(`Sunlight is ${Math.round(m.sunlight_pct)} %, below the ${thresholds.viable_sunlight_pct_min} % target.`);
  }
  if (m.longest_darkness_h > thresholds.viable_longest_darkness_h_max) {
    short.push(`Longest night is ${Math.round(m.longest_darkness_h)} h, above the ${thresholds.viable_longest_darkness_h_max} h target.`);
  }
  if (m.earth_visibility_pct < thresholds.viable_earth_visibility_pct_min) {
    short.push(`Earth is visible ${Math.round(m.earth_visibility_pct)} % of the time, below the ${thresholds.viable_earth_visibility_pct_min} % target.`);
  }
  if (m.longest_comms_gap_h > thresholds.viable_longest_comms_gap_h_max) {
    short.push(`Longest comms gap is ${Math.round(m.longest_comms_gap_h)} h, above the ${thresholds.viable_longest_comms_gap_h_max} h limit.`);
  }
  if (short.length) {
    return {
      level: "marginal",
      reasons: short,
      summary: tag + "Marginal: " + short[0],
      thresholds,
    };
  }
  return {
    level: "viable",
    reasons: ["All power and communications targets met."],
    summary: tag + "Viable on the configured thresholds.",
    thresholds,
  };
}

type WithRows = {
  rows?: {
    scenario: { site: string };
    metrics: Metrics;
    verdict?: Verdict;
    wsm_score?: number;
    wsm_rank?: number;
    topsis_score?: number;
    topsis_rank?: number;
    win_fraction?: number;
  }[];
  ranking?: Record<string, unknown>;
};

function addPlaceholderVerdicts<T extends WithRows>(data: T, body?: unknown): T {
  const req = (body ?? {}) as { thresholds?: Record<string, number>; profile?: string };
  const profileName = req.profile === "science_solar" ? "science_solar" : "engineering_ops";
  const weights: Record<string, number> =
    profileName === "science_solar"
      ? {
          power_W_m2_vertical_integrated_kWh_m2: 0.15,
          longest_darkness_h: 0.1,
          longest_comms_gap_h: 0.1,
          joint_power_comms_pct: 0.25,
          sunlight_pct: 0.25,
          earth_visibility_pct: 0.15,
        }
      : {
          power_W_m2_vertical_integrated_kWh_m2: 0.1,
          longest_darkness_h: 0.25,
          longest_comms_gap_h: 0.25,
          joint_power_comms_pct: 0.25,
          sunlight_pct: 0.1,
          earth_visibility_pct: 0.05,
        };

  const rows = data.rows ?? [];
  for (const row of rows) {
    row.verdict = placeholderVerdict(row.metrics, req.thresholds);
  }

  if (rows.length > 0) {
    const keys = Object.keys(weights) as (keyof Metrics)[];
    const lowerIsBetter = new Set<keyof Metrics>(["longest_darkness_h", "longest_comms_gap_h"]);
    const norm: Record<string, number[]> = {};
    for (const k of keys) {
      const vals = rows.map((r) => Number(r.metrics[k] ?? 0));
      const minV = Math.min(...vals);
      const maxV = Math.max(...vals);
      const span = maxV - minV;
      norm[k] = vals.map((v) => {
        if (span < 1e-9) return 1.0;
        return lowerIsBetter.has(k) ? (maxV - v) / span : (v - minV) / span;
      });
    }
    rows.forEach((r, i) => {
      let wsm = 0;
      let dPlusSq = 0;
      let dMinusSq = 0;
      for (const k of keys) {
        const w = weights[k];
        const u = norm[k][i];
        wsm += w * u;
        dPlusSq += (w * (1 - u)) ** 2;
        dMinusSq += (w * u) ** 2;
      }
      const dPlus = Math.sqrt(dPlusSq);
      const dMinus = Math.sqrt(dMinusSq);
      r.wsm_score = wsm;
      r.topsis_score = dPlus + dMinus > 0 ? dMinus / (dPlus + dMinus) : 0.5;
    });
    const byWsm = [...rows].sort((a, b) => (b.wsm_score ?? 0) - (a.wsm_score ?? 0));
    byWsm.forEach((r, idx) => (r.wsm_rank = idx + 1));
    const byTopsis = [...rows].sort((a, b) => (b.topsis_score ?? 0) - (a.topsis_score ?? 0));
    byTopsis.forEach((r, idx) => {
      r.topsis_rank = idx + 1;
      r.win_fraction = idx === 0 ? 0.68 : idx === 1 ? 0.32 : 0;
    });
    data.ranking = {
      profile: {
        name: profileName,
        label: profileName === "science_solar" ? "Science (Solar)" : "Engineering (Ops)",
        description:
          profileName === "science_solar"
            ? "Maximises total solar exposure and integrated energy."
            : "Minimises worst-case darkness and communications outages.",
        weights,
      },
      top_scenario_index: rows.indexOf(byTopsis[0]),
      summary: `With the ${profileName === "science_solar" ? "science" : "engineering"} weights, ${byTopsis[0]?.scenario?.site ?? "the top site"} ranks #1.`,
    };
  }
  return data;
}

export async function resolveFixture<T>(files: FixtureFiles, method: "GET" | "POST", path: string, params?: Params, body?: unknown): Promise<T> {
  const clean = path.split("?")[0];
  let m: RegExpMatchArray | null;

  if (method === "GET" && clean === "/sites") {
    const data = await load<{ sites: { category: string }[] }>(files, "sites.json");
    const cat = params?.category;
    return (cat ? { ...data, sites: data.sites.filter((s) => s.category === cat) } : data) as T;
  }
  if (method === "GET" && (m = clean.match(/^\/sites\/([^/]+)$/))) {
    const data = await load<{ sites: { id: string | null }[] }>(files, "sites.json");
    const site = data.sites.find((s) => s.id === m![1]);
    if (!site) throw new FixtureMissingError(`Site ${m[1]} not in sites.json`);
    return { status: "ok", site } as T;
  }
  if (method === "POST" && clean === "/scenarios/conditions") return loadForSite<T>(files, "site_conditions", body);
  if (method === "POST" && clean === "/scenarios/timeline") return loadForSite<T>(files, "site_timeline", body);
  if (method === "POST" && clean === "/scenarios/compare") {
    // One example comparison, whatever scenarios were sent.
    return addPlaceholderVerdicts(await load<WithRows>(files, "compare_four_sites.json"), body) as T;
  }
  if (method === "POST" && clean === "/scenarios/date-sweep") {
    return addPlaceholderVerdicts(await loadForSite<WithRows>(files, "date_sweep", body), body) as T;
  }
  if (method === "GET" && clean === "/terrain/heightmap") {
    const lat = Number(params?.lat_deg ?? -89.45);
    const lon = Number(params?.lon_deg ?? -137.3);
    return {
      status: lat <= -80 ? "dem_unavailable" : "outside_nominal_coverage",
      lat_deg: lat,
      lon_deg: lon,
      radius_m: Number(params?.radius_m ?? 1600),
      rows: 0,
      cols: 0,
      resolution_m: null,
      values_m: [],
    } as T;
  }
  throw new FixtureMissingError(`No fixture mapping for ${method} ${clean}`);
}

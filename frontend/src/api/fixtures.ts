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
export function placeholderVerdict(m: Pick<Metrics, "sunlight_pct" | "longest_darkness_h" | "earth_visibility_pct" | "longest_comms_gap_h">): Verdict {
  const thresholds = {
    not_viable_longest_darkness_h_above: 100,
    not_viable_sunlight_pct_below: 30,
    not_viable_earth_visibility_pct_below: 20,
    viable_sunlight_pct_min: 60,
    viable_longest_darkness_h_max: 50,
    viable_earth_visibility_pct_min: 50,
    viable_longest_comms_gap_h_max: 72,
  };
  const bad: string[] = [];
  if (m.longest_darkness_h > 100) bad.push(`Longest night ${Math.round(m.longest_darkness_h)} h > 100 h limit`);
  if (m.sunlight_pct < 30) bad.push(`Sunlight ${Math.round(m.sunlight_pct)} % < 30 %`);
  if (m.earth_visibility_pct < 20) bad.push(`Earth visible ${Math.round(m.earth_visibility_pct)} % < 20 %`);
  const tag = "[placeholder verdict, fixture mode] ";
  if (bad.length) return { level: "not_viable", reasons: bad, summary: tag + "Not viable: " + bad[0] + ".", thresholds };

  const short: string[] = [];
  if (m.sunlight_pct < 60) short.push(`Sunlight ${Math.round(m.sunlight_pct)} % < 60 %`);
  if (m.longest_darkness_h > 50) short.push(`Longest night ${Math.round(m.longest_darkness_h)} h > 50 h`);
  if (m.earth_visibility_pct < 50) short.push(`Earth visible ${Math.round(m.earth_visibility_pct)} % < 50 %`);
  if (m.longest_comms_gap_h > 72) short.push(`Longest comms gap ${Math.round(m.longest_comms_gap_h)} h > 72 h`);
  if (short.length) return { level: "marginal", reasons: short, summary: tag + "Marginal: " + short[0] + ".", thresholds };
  return { level: "viable", reasons: ["All thresholds met"], summary: tag + "Viable on the placeholder thresholds.", thresholds };
}

type WithRows = { rows?: { metrics: Metrics; verdict?: Verdict }[] };
function addPlaceholderVerdicts<T extends WithRows>(data: T): T {
  for (const row of data.rows ?? []) if (!row.verdict) row.verdict = placeholderVerdict(row.metrics);
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
    return addPlaceholderVerdicts(await load<WithRows>(files, "compare_four_sites.json")) as T;
  }
  if (method === "POST" && clean === "/scenarios/date-sweep") {
    return addPlaceholderVerdicts(await loadForSite<WithRows>(files, "date_sweep", body)) as T;
  }
  throw new FixtureMissingError(`No fixture mapping for ${method} ${clean}`);
}

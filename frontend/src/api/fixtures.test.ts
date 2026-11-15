import { describe, expect, it } from "vitest";
import { FixtureMissingError, placeholderVerdict, resolveFixture, type FixtureFiles } from "./fixtures";

const file = (o: unknown) => async () => JSON.stringify(o);
const m = (o: object = {}) => ({ sunlight_pct: 100, longest_darkness_h: 0, earth_visibility_pct: 60, longest_comms_gap_h: 347, ...o });

const files: FixtureFiles = {
  "../../../mock_data/astro/sites.json": file({ status: "ok", sites: [{ id: "im-1", category: "clps" }, { id: "apollo-11", category: "apollo" }] }),
  "../../../mock_data/astro/site_conditions_im-1.json": file({ site: "im-1" }),
  "../../../mock_data/astro/compare_four_sites.json": file({ rows: [{ metrics: m() }, { metrics: m({ longest_darkness_h: 250 }) }] }),
  "../../../mock_data/astro/date_sweep_im-1.json": file({ rows: [{ metrics: m({ longest_comms_gap_h: 10 }) }] }),
};

describe("placeholderVerdict (README 6.5 default rule)", () => {
  it("marginal: full sun but a long comms gap", () => expect(placeholderVerdict(m()).level).toBe("marginal"));
  it("not viable: a night longer than 100 h", () => expect(placeholderVerdict(m({ longest_darkness_h: 250 })).level).toBe("not_viable"));
  it("viable when every threshold is met", () => expect(placeholderVerdict(m({ longest_comms_gap_h: 10 })).level).toBe("viable"));
  it("always says it is a placeholder", () => expect(placeholderVerdict(m()).summary).toContain("placeholder"));
});

describe("resolveFixture", () => {
  it("filters sites by category", async () => {
    const r = await resolveFixture<{ sites: unknown[] }>(files, "GET", "/sites", { category: "apollo" });
    expect(r.sites).toHaveLength(1);
  });
  it("loads conditions by catalog id", async () => {
    expect(await resolveFixture(files, "POST", "/scenarios/conditions", undefined, { site: "im-1" })).toEqual({ site: "im-1" });
  });
  it("custom coordinates need the live API", async () => {
    await expect(resolveFixture(files, "POST", "/scenarios/conditions", undefined, { site: { lat_deg: -89, lon_deg: 0 } })).rejects.toThrow(/live API/);
  });
  it("unknown site gives a clear fixture error", async () => {
    await expect(resolveFixture(files, "POST", "/scenarios/timeline", undefined, { site: "im-1" })).rejects.toBeInstanceOf(FixtureMissingError);
  });
  it("compare and date sweep rows get a placeholder verdict", async () => {
    const c = await resolveFixture<{ rows: { verdict: { level: string } }[] }>(files, "POST", "/scenarios/compare", undefined, {});
    expect(c.rows.map((r) => r.verdict.level)).toEqual(["marginal", "not_viable"]);
    const s = await resolveFixture<{ rows: { verdict: { level: string } }[] }>(files, "POST", "/scenarios/date-sweep", undefined, { site: "im-1" });
    expect(s.rows[0].verdict.level).toBe("viable");
  });
});

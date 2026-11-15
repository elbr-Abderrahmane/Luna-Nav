import type { Compare, DateSweep } from "../api/types";
import { useAssistantStore } from "../state/assistantStore";
import { METRICS, VERDICT_TEXT } from "./metrics";

const NA = "Not available";

const cell = (v: string): string => (/[",\r\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
const toCsv = (rows: string[][]): string => "﻿" + rows.map((r) => r.map(cell).join(",")).join("\r\n") + "\r\n";
const num = (v: number | null | undefined, digits: number): string => (v === null || v === undefined || Number.isNaN(v) ? NA : v.toFixed(digits));

export function compareCsv(d: Compare): string {
  const rows: string[][] = [["Metric", "Unit", ...d.rows.map((r) => `${r.site.name} (${r.start_utc.slice(0, 10)})`)]];
  rows.push(["Verdict", "", ...d.rows.map((r) => (r.verdict ? (VERDICT_TEXT[r.verdict.level] ?? r.verdict.level) : NA))]);
  rows.push(["Verdict reasons", "", ...d.rows.map((r) => (r.verdict ? r.verdict.reasons.join("; ") : ""))]);
  for (const m of METRICS) {
    rows.push([m.label, m.unit, ...d.rows.map((r) => num(r.metrics[m.key as keyof typeof r.metrics] as number | null, m.digits))]);
  }
  rows.push(["Horizon method", "", ...d.rows.map((r) => r.method)]);
  rows.push(["Warnings", "", ...d.rows.map((r) => r.warnings.join("; "))]);
  rows.push([]);
  rows.push(["Source", "", d.data_sources?.ephemeris_source ?? NA]);
  return toCsv(rows);
}

export function sweepCsv(d: DateSweep): string {
  const rows: string[][] = [
    ["Site", "Landing date (UTC)", "Verdict", "Power + comms (%)", "Sunlight (%)", "Earth visible (%)", "Longest night (h)", "Longest comms gap (h)", "Warnings"],
  ];
  for (const r of d.rows) {
    rows.push([
      d.site.name,
      r.start_utc.slice(0, 10),
      r.verdict ? (VERDICT_TEXT[r.verdict.level] ?? r.verdict.level) : NA,
      num(r.metrics.power_and_comms_pct, 0),
      num(r.metrics.sunlight_pct, 0),
      num(r.metrics.earth_visibility_pct, 0),
      num(r.metrics.longest_darkness_h, 0),
      num(r.metrics.longest_comms_gap_h, 0),
      r.warnings.join("; "),
    ]);
  }
  return toCsv(rows);
}

export function summaryText(d: Compare): string {
  const lines = [`LunaNav comparison of ${d.rows.length} scenarios`];
  d.rows.forEach((r, i) => {
    const m = r.metrics;
    const verdict = r.verdict ? `${VERDICT_TEXT[r.verdict.level] ?? r.verdict.level}. ` : "";
    lines.push(
      `${i + 1}. ${r.site.name}, landing ${r.start_utc.slice(0, 10)}: ${verdict}power + comms ${num(m.power_and_comms_pct, 0)}%, sunlight ${num(m.sunlight_pct, 0)}%, Earth visible ${num(m.earth_visibility_pct, 0)}%, longest night ${num(m.longest_darkness_h, 0)} h.`,
    );
  });
  const best = d.best?.power_and_comms_pct;
  if (best) lines.push(`Best power + comms: ${best.label}.`);
  lines.push("Geometry only (ephemeris and terrain): not a power system or radio link analysis.");
  return lines.join("\n");
}

/** Saves a text file through the browser. Tells the guide so the tour can move on. */
export function downloadText(filename: string, text: string, mime = "text/csv;charset=utf-8"): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  useAssistantStore.getState().noteExport();
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    useAssistantStore.getState().noteExport();
    return true;
  } catch {
    return false; // clipboard can be blocked; the caller shows a hint
  }
}

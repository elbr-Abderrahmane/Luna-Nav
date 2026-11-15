import type { Verdict } from "../api/types";
import { VERDICT_TEXT } from "../lib/metrics";

/** The verdict comes from the API (P4's rule). The frontend only displays it, with its reasons. */
export function VerdictBadge({ verdict }: { verdict: Verdict | undefined }) {
  if (!verdict) return <span className="badge">No verdict</span>;
  const cls = verdict.level === "viable" ? "ok" : verdict.level === "marginal" ? "warn" : "bad";
  return <span className={`badge ${cls}`}>{VERDICT_TEXT[verdict.level] ?? verdict.level}</span>;
}

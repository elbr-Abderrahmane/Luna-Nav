"""Scenario Orchestration Service (P5 Integration of P2 Terrain, P3 Astro, and P4 Decision).

Implements the unified data flow described in README §3 and §6:
1. Calls P3 (`lunanav.astro`) for site catalog, site conditions, timeline, comparison, and date sweep.
2. Calls P4 (`lunanav.decision`) to attach viability verdicts (`viable` / `marginal` / `not_viable`),
   plain-language summaries/explanations, and WSM/TOPSIS multi-criteria rankings + sensitivity analysis.
3. Calls P2 (`lunanav.terrain`) to attach local DEM coverage and descriptive terrain metrics when available.
4. Caches computed results on disk (`data/cache/scenarios/`) per README §3 Rule 6.
"""

from __future__ import annotations

import copy
import csv
import io
import logging
from typing import Any, Dict, List, Optional

from app.core.cache import cached_call
from lunanav.astro import (
    SYNODIC_MONTH_D,
    compare_scenarios,
    date_sweep,
    get_site,
    list_sites,
    site_conditions,
    site_timeline,
)
from lunanav.decision import (
    DecisionInputError,
    explain_comparison,
    explain_ranking,
    explain_verdict,
    rank_scenarios,
    sensitivity_analysis,
    verdict,
)
from lunanav.terrain import local_slope, site_coverage, terrain_summary

logger = logging.getLogger("luna_nav.services.scenarios")


def _normalize_site_arg(site: Any) -> Any:
    """Convert Pydantic model or dict into plain dict or string expected by P3."""
    if hasattr(site, "model_dump"):
        return site.model_dump(exclude_none=True)
    return site


def _enrich_terrain(site_info: Dict[str, Any]) -> Dict[str, Any]:
    """Attach P2 terrain coverage and optional local metrics for a resolved site."""
    lat = site_info.get("lat_deg")
    lon = site_info.get("lon_deg")
    if lat is None or lon is None:
        return {"status": "unavailable"}
    try:
        cov = site_coverage(float(lat), float(lon))
        slope_info = local_slope(float(lat), float(lon)) if cov.get("pixel_covered") else {"status": cov["status"], "slope_deg": None}
        summary_info = (
            terrain_summary(float(lat), float(lon), radius_m=240.0)
            if cov.get("raster_coverage")
            else {
                "status": cov["status"],
                "valid_pixel_count": 0,
                "min_elevation_m": None,
                "max_elevation_m": None,
                "mean_elevation_m": None,
                "roughness_m": None,
            }
        )
        return {
            "coverage": cov,
            "slope_deg": slope_info.get("slope_deg"),
            "slope_status": slope_info.get("status"),
            "roughness_m": summary_info.get("roughness_m"),
            "summary": summary_info,
        }
    except Exception as exc:
        logger.debug("P2 terrain enrichment skipped: %s", exc)
        return {"status": "unavailable"}


def _attach_row_verdicts(
    rows: List[Dict[str, Any]], thresholds: Optional[Dict[str, float]] = None
) -> None:
    """Attach P4's `verdict` to each row in-place."""
    for row in rows:
        metrics = row.get("metrics")
        if isinstance(metrics, dict):
            v = verdict(metrics, thresholds)
            row["verdict"] = v
            row["verdict_explanation"] = explain_verdict(v)


def _attach_comparison_decision_analysis(
    result: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
    profile: str = "engineering",
) -> Dict[str, Any]:
    """Enrich a `compare_scenarios` or `date_sweep` result with P4 verdicts, explanation, and ranking."""
    out = copy.deepcopy(result)
    rows = out.get("rows", [])
    if not rows:
        return out

    _attach_row_verdicts(rows, thresholds)

    try:
        out["explanation"] = explain_comparison(rows)
    except Exception as exc:
        logger.warning("explain_comparison failed: %s", exc)

    if len(rows) >= 2:
        try:
            # Ensure unique labels for ranking if any labels collide
            ranking_rows = []
            seen: set[str] = set()
            for idx, r in enumerate(rows):
                lbl = r.get("label") or f"scenario-{idx + 1}"
                if lbl in seen:
                    lbl = f"{lbl} ({idx + 1})"
                seen.add(lbl)
                ranking_rows.append({**r, "label": lbl})

            ranking = rank_scenarios(ranking_rows, profile=profile, method="both")
            sens = sensitivity_analysis(ranking_rows, profile=profile, method="topsis")
            out["ranking"] = ranking
            out["sensitivity"] = sens
            out["ranking_explanation"] = explain_ranking(ranking, sens)
        except Exception as exc:
            logger.warning("P4 ranking/sensitivity skipped: %s", exc)

    return out


class ScenarioService:
    """Unified service orchestrating P3 (Astronomy), P4 (Decision), and P2 (Terrain)."""

    def get_sites(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Return the 26-site lunar catalog (optionally filtered by category)."""
        try:
            sites = list_sites(category=category)
        except ValueError as exc:
            return {
                "status": "error",
                "error": {"code": "INVALID_CATEGORY", "message": str(exc)},
            }
        return {"status": "ok", "sites": sites}

    def get_site_by_id(self, site_id: str) -> Dict[str, Any]:
        """Return a single catalog site by its kebab-case ID."""
        try:
            site = get_site(site_id)
        except KeyError:
            return {
                "status": "error",
                "error": {"code": "UNKNOWN_SITE", "message": f"Unknown site id '{site_id}'"},
            }
        return {"status": "ok", "site": site}

    def compute_conditions(
        self,
        site: Any,
        start_utc: str,
        window_days: Optional[float] = None,
        step_h: float = 0.5,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute Screen 2 (`site_conditions`) + P4 verdict + P2 terrain metadata."""
        site_arg = _normalize_site_arg(site)
        win_days = float(window_days) if window_days is not None else SYNODIC_MONTH_D

        base = cached_call(
            "conditions",
            {"site": site_arg, "start_utc": start_utc, "window_days": win_days, "step_h": step_h},
            lambda: site_conditions(site_arg, start_utc, window_days=win_days, step_h=step_h),
        )
        if base.get("status") != "ok":
            return base

        out = copy.deepcopy(base)
        if isinstance(out.get("metrics"), dict):
            v = verdict(out["metrics"], thresholds)
            out["verdict"] = v
            out["verdict_explanation"] = explain_verdict(v)
        if isinstance(out.get("site"), dict):
            out["terrain"] = _enrich_terrain(out["site"])
        return out

    def compute_timeline(
        self,
        site: Any,
        start_utc: str,
        days: Optional[float] = None,
        step_h: float = 1.0,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute Screen 3 (`site_timeline`) + P4 verdict."""
        site_arg = _normalize_site_arg(site)
        win_days = float(days) if days is not None else SYNODIC_MONTH_D

        base = cached_call(
            "timeline",
            {"site": site_arg, "start_utc": start_utc, "days": win_days, "step_h": step_h},
            lambda: site_timeline(site_arg, start_utc, days=win_days, step_h=step_h),
        )
        if base.get("status") != "ok":
            return base

        out = copy.deepcopy(base)
        if isinstance(out.get("metrics"), dict):
            v = verdict(out["metrics"], thresholds)
            out["verdict"] = v
            out["verdict_explanation"] = explain_verdict(v)
        return out

    def compute_compare(
        self,
        scenarios: List[Dict[str, Any]],
        window_days: Optional[float] = None,
        step_h: float = 1.0,
        thresholds: Optional[Dict[str, float]] = None,
        profile: str = "engineering",
    ) -> Dict[str, Any]:
        """Compute Screen 4 (`compare_scenarios`) + P4 verdicts, explanations, and WSM/TOPSIS rankings."""
        win_days = float(window_days) if window_days is not None else SYNODIC_MONTH_D
        normalized_scenarios = []
        for s in scenarios:
            if not isinstance(s, dict):
                normalized_scenarios.append(s)
                continue
            item = dict(s)
            if "site" in item:
                item["site"] = _normalize_site_arg(item["site"])
            if item.get("window_days") is None:
                item.pop("window_days", None)
            if item.get("label") is None:
                item.pop("label", None)
            normalized_scenarios.append(item)

        base = cached_call(
            "compare",
            {"scenarios": normalized_scenarios, "window_days": win_days, "step_h": step_h},
            lambda: compare_scenarios(normalized_scenarios, window_days=win_days, step_h=step_h),
        )
        if base.get("status") != "ok":
            return base

        return _attach_comparison_decision_analysis(base, thresholds=thresholds, profile=profile)

    def compute_date_sweep(
        self,
        site: Any,
        first_start_utc: str,
        n: int = 12,
        every_days: Optional[float] = None,
        window_days: Optional[float] = None,
        step_h: float = 1.0,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute Screen 5 (`date_sweep`) + P4 verdicts and seasonal explanations."""
        site_arg = _normalize_site_arg(site)
        ev_days = float(every_days) if every_days is not None else SYNODIC_MONTH_D

        base = cached_call(
            "date_sweep",
            {
                "site": site_arg,
                "first_start_utc": first_start_utc,
                "n": n,
                "every_days": ev_days,
                "window_days": window_days,
                "step_h": step_h,
            },
            lambda: date_sweep(
                site_arg,
                first_start_utc,
                n=n,
                every_days=ev_days,
                window_days=window_days,
                step_h=step_h,
            ),
        )
        if base.get("status") != "ok":
            return base

        return _attach_comparison_decision_analysis(base, thresholds=thresholds, profile="science")

    def compute_ranking(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
        scenarios: Optional[List[Dict[str, Any]]] = None,
        window_days: Optional[float] = None,
        step_h: float = 1.0,
        profile: str = "engineering",
        weights: Optional[Dict[str, float]] = None,
        method: str = "both",
        include_sensitivity: bool = True,
    ) -> Dict[str, Any]:
        """Run P4's WSM & TOPSIS multi-criteria ranking and sensitivity analysis on 2..N scenarios."""
        target_rows = rows
        if target_rows is None and scenarios is not None:
            cmp_res = self.compute_compare(
                scenarios, window_days=window_days, step_h=step_h, profile=profile
            )
            if cmp_res.get("status") != "ok":
                return cmp_res
            target_rows = cmp_res.get("rows", [])

        if not target_rows:
            raise DecisionInputError("Provide either 'rows' or 'scenarios' with at least 2 items.")

        ranking = rank_scenarios(target_rows, profile=profile, weights=weights, method=method)
        sens = None
        if include_sensitivity:
            sens_method = "topsis" if method in ("topsis", "both") else "wsm"
            sens = sensitivity_analysis(target_rows, profile=profile, method=sens_method)

        explanation = explain_ranking(ranking, sens)
        return {
            "status": "ok",
            **ranking,
            "sensitivity": sens,
            "explanation": explanation,
        }

    def export_comparison_csv(self, compare_data: Dict[str, Any]) -> str:
        """Format a `Compare` payload (with P4 verdicts) as a clean CSV document."""
        rows = compare_data.get("rows", [])
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "label",
                "site_id",
                "site_name",
                "lat_deg",
                "lon_deg",
                "elevation_m",
                "start_utc",
                "method",
                "verdict_level",
                "verdict_summary",
                "sunlight_pct",
                "longest_darkness_h",
                "earth_visibility_pct",
                "longest_comms_gap_h",
                "power_and_comms_pct",
                "vertical_panel_energy_kwh_m2",
                "sun_elevation_deg_max",
                "warnings",
            ]
        )
        for r in rows:
            site = r.get("site") or {}
            m = r.get("metrics") or {}
            v = r.get("verdict") or {}
            writer.writerow(
                [
                    r.get("label", ""),
                    site.get("id", ""),
                    site.get("name", ""),
                    site.get("lat_deg", ""),
                    site.get("lon_deg", ""),
                    site.get("elevation_m", ""),
                    r.get("start_utc", ""),
                    r.get("method", ""),
                    v.get("level", ""),
                    v.get("summary", ""),
                    m.get("sunlight_pct", ""),
                    m.get("longest_darkness_h", ""),
                    m.get("earth_visibility_pct", ""),
                    m.get("longest_comms_gap_h", ""),
                    m.get("power_and_comms_pct", ""),
                    m.get("vertical_panel_energy_kwh_m2", ""),
                    m.get("sun_elevation_deg_max", ""),
                    "; ".join(r.get("warnings") or []),
                ]
            )
        return buffer.getvalue()

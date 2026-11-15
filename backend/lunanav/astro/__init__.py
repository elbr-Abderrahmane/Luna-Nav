"""LunaNav astronomy & physics (P3). Public API = README §7.8.

    plan_mission(arrival_utc, transfer_days=4.0) -> MissionPlan
    sun_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> (az_deg, el_deg)
    earth_az_el(lat_deg, lon_deg, elevation_m, t_utc) -> (az_deg, el_deg)
    horizon_mask(lat_deg, lon_deg, n_az=360, max_dist_km=100) -> np.ndarray
    illumination_at(lat_deg, lon_deg, elevation_m, arrival_utc, use_horizon=True) -> IlluminationSummary
    illumination_area(samples, arrival_utc) -> IlluminationSummary

P5 questionnaire wrappers (JSON-ready dicts with status/warnings/frames/units):
    calculate_mission(arrival_datetime, parameters=None)
    analyze_illumination(latitude, longitude, start_datetime, end_datetime, terrain_data=None)
    analyze_earth_visibility(latitude, longitude, observation_datetime, terrain_data=None)

Scenario tools for the official challenge (site + date comparison, countdowns, windows):
    site_conditions(site, start_datetime, window_days=29.53, step_h=0.5, terrain_data=None)
    site_timeline(site, start_datetime, days=29.53, step_h=1.0, terrain_data=None)
    compare_scenarios([{"site", "start_utc", "label"?}, ...], window_days=29.53)
    date_sweep(site, first_start_datetime, n=12, every_days=29.53)
    list_sites(category=None), get_site(site_id), resolve_site(site)
"""

from .ephemeris import get_ephemeris
from .horizon import horizon_mask
from .illumination import illumination_area, illumination_at
from .integration import (
    analyze_earth_visibility,
    analyze_illumination,
    calculate_mission,
)
from .mission import plan_mission
from .scenarios import SYNODIC_MONTH_D, compare_scenarios, date_sweep, site_conditions, site_timeline
from .sites import get_site, list_sites, resolve_site
from .topo import earth_az_el, sun_az_el

__all__ = [
    "SYNODIC_MONTH_D",
    "analyze_earth_visibility",
    "analyze_illumination",
    "calculate_mission",
    "compare_scenarios",
    "date_sweep",
    "earth_az_el",
    "get_ephemeris",
    "get_site",
    "horizon_mask",
    "illumination_area",
    "illumination_at",
    "list_sites",
    "plan_mission",
    "resolve_site",
    "site_conditions",
    "site_timeline",
    "sun_az_el",
]

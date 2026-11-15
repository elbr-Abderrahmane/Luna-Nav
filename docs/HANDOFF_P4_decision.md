# LunaNav handoff: P3 (astronomy) to P4 (decision)

From wrida (P3). The official challenge is about comparing **sites and dates** for **power** (Sun)
and **direct-to-Earth comms** (Earth visibility). So scoring should now weight lighting and comms
first, and terrain second. Full team plan: https://claude.ai/artifact/GBzBsr5GtkNrBvWXaR6pWC

## What's in this zip

| File | What |
|---|---|
| `compare_four_sites.json` | Real output: 4 sites compared on the same date (one row each + best per metric). |
| `date_sweep_connecting-ridge.json` | Real output: one site over 12 lunar days (seasons, "launch slipped" story). |
| `site_conditions_im-1.json` | Full output for one scenario, so you see every field. |

All were computed with the real LOLA terrain and validated ephemeris.

## Metrics you can score on

Each scenario row has `metrics` (over the analysis window, default one lunar day = 29.53 d) plus
values at the start time. A scenario is one site + one start date.

| Field (in `row["metrics"]`) | Meaning | Unit | Better |
|---|---|---|---|
| `sunlight_pct` | Share of the window with the Sun's centre above the local horizon | % | higher |
| `sunlight_hours` | Same, in hours | h | higher |
| `longest_darkness_h` | Longest continuous period without Sun (battery and heater sizing) | h | lower |
| `earth_visibility_pct` | Share of the window with Earth above the local horizon (direct-to-Earth comms) | % | higher |
| `earth_visible_hours` | Same, in hours | h | higher |
| `longest_comms_gap_h` | Longest continuous period without Earth in view | h | lower |
| `power_and_comms_pct` | Share of the window with **both** Sun and Earth up | % | higher |
| `vertical_panel_energy_kwh_m2` | Solar energy on a Sun-facing vertical panel over the window | kWh/m2 | higher |
| `mean_vertical_panel_factor` | Mean cos(Sun elevation) x visible disk fraction (0..1) | - | higher |
| `mean_horizontal_panel_factor` | Same for a flat panel (near 0 at the pole) | - | higher |
| `sun_elevation_deg_max` / `_min` / `_mean_when_lit` | Solar elevation stats | deg | context |
| `earth_elevation_deg_max` / `_min` | Earth elevation stats | deg | context |
| `n_sunsets`, `n_earthsets` | Number of sunsets / Earthsets in the window | count | lower |
| `libration_lat_range_deg`, `libration_lon_range_deg` | How far Earth wobbles in the sky | deg | context |

Values at the start time (row level, useful for "can we land now?"):

| Field | Meaning | Unit |
|---|---|---|
| `sunlit_at_start`, `earth_visible_at_start` | Sun / Earth up at the landing time | bool |
| `sun_elevation_deg_at_start`, `earth_elevation_deg_at_start` | Elevations at landing | deg |
| `sun_countdown.time_remaining_h` | Hours to next sunset (if lit) or sunrise (if dark); `null` + `beyond_window: true` if none | h |
| `sun_countdown.next_event` | `"sunset"` or `"sunrise"` | text |
| `earth_countdown.time_remaining_h` / `.next_event` | Same for Earthset / Earthrise | h / text |

`compare_scenarios` and `date_sweep` already return `best`: the winning scenario per metric, with
`direction` (`higher_is_better` / `lower_is_better`). You can reuse it or ignore it.

## Suggested changes on your side (in priority order)

1. **New criteria** from the table above: `sunlight_pct`, `longest_darkness_h`,
   `earth_visibility_pct`, `longest_comms_gap_h`, `power_and_comms_pct`, plus
   `sun_countdown.time_remaining_h` at landing (a sunset soon after landing is bad). Give them most
   of the weight. Terrain criteria (slope, roughness) become secondary.
2. **Compare 2 to N scenarios** (any site, any date), instead of exactly 3 zones.
3. **Viability verdict** per scenario: viable, marginal or not viable, with the reason in words,
   for example "sunset 19 h after landing" or "Earth below the horizon for 14 days". Placeholder
   thresholds until we tune them: not viable if `sunlit_at_start` is false or the Sun sets within
   48 h of landing; marginal if `longest_darkness_h` > 100 or `earth_visibility_pct` < 30.
4. **"Why" explanations for the public**: why a small move or a one-month slip changes everything.
   The date sweep file shows the connecting ridge going from about 36 % (May) to 100 % (Aug to Jan) sunlight across the year.
5. Optional: a "science" vs "engineering" weight preset.

Far-side sites (Chang'e 4, Chang'e 6) always have `earth_visibility_pct = 0`: they need a relay.
Mark them so instead of just scoring them low.

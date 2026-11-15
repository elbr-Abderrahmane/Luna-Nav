var e=`{
 "status": "ok",
 "result_type": "ephemeris_calculation",
 "warnings": [],
 "site": {
  "id": "im-1",
  "name": "IM-1 Odysseus (Malapert A area)",
  "category": "clps",
  "mission": "IM-1",
  "agency": "Intuitive Machines / NASA CLPS",
  "coord_quality": "landed",
  "lat_deg": -80.13,
  "lon_deg": 1.44,
  "elevation_m": 2591.95
 },
 "method": "horizon_mask",
 "window": {
  "start_utc": "2027-01-10T00:00:00Z",
  "end_utc": "2027-02-08T12:44:03Z",
  "duration_h": 708.734,
  "duration_days": 29.5306,
  "sampling_interval_h": 0.5,
  "n_samples": 1419
 },
 "now": {
  "t_utc": "2027-01-10T00:00:00Z",
  "sun": {
   "azimuth_deg": 151.763,
   "elevation_deg": -7.844,
   "horizon_elevation_deg": 11.05,
   "margin_above_horizon_deg": -18.894,
   "visible": false,
   "disk_visible_fraction": 0.0,
   "apparent_radius_deg": 0.2716,
   "distance_km": 146742662.2
  },
  "earth": {
   "azimuth_deg": 355.323,
   "elevation_deg": 8.587,
   "horizon_elevation_deg": -0.029,
   "margin_above_horizon_deg": 8.616,
   "visible": true,
   "disk_visible_fraction": 1.0,
   "apparent_radius_deg": 0.9034,
   "distance_km": 404096.9
  },
  "power": {
   "irradiance_w_m2": 0.0,
   "vertical_panel_factor": 0.0,
   "horizontal_panel_factor": 0.0,
   "vertical_panel_w_m2": 0.0
  },
  "libration": {
   "sub_earth_lat_deg": 1.007,
   "sub_earth_lon_deg": -3.182
  },
  "sub_solar": {
   "lat_deg": -0.868,
   "lon_deg": 153.487
  }
 },
 "countdown": {
  "sun": {
   "next_event": "sunrise",
   "next_event_utc": "2027-01-17T09:47:07Z",
   "time_remaining_h": 177.785,
   "time_remaining_text": "7 d 9 h 47 min",
   "beyond_window": false,
   "summary": "Sunrise in 7 d 9 h 47 min"
  },
  "earth": {
   "next_event": "earthset",
   "next_event_utc": null,
   "time_remaining_h": null,
   "time_remaining_text": null,
   "beyond_window": true,
   "summary": "Earth stays up for the whole 29.5-day window"
  }
 },
 "next_events": [
  {
   "event": "sunrise",
   "t_utc": "2027-01-17T09:47:07Z",
   "in_h": 177.785,
   "in_text": "7 d 9 h 47 min"
  },
  {
   "event": "sunset",
   "t_utc": "2027-01-29T05:54:37Z",
   "in_h": 461.91,
   "in_text": "19 d 5 h 55 min"
  }
 ],
 "windows": {
  "sunlit": [
   {
    "start_utc": "2027-01-17T09:47:07Z",
    "end_utc": "2027-01-29T05:54:37Z",
    "duration_h": 284.125,
    "duration_text": "11 d 20 h 8 min",
    "starts_in_h": 177.785,
    "open_at_window_start": false,
    "open_at_window_end": false
   }
  ],
  "earth_visible": [
   {
    "start_utc": "2027-01-10T00:00:00Z",
    "end_utc": "2027-02-08T12:44:03Z",
    "duration_h": 708.734,
    "duration_text": "29 d 12 h 44 min",
    "starts_in_h": 0.0,
    "open_at_window_start": true,
    "open_at_window_end": true
   }
  ],
  "power_and_comms": [
   {
    "start_utc": "2027-01-17T09:47:07Z",
    "end_utc": "2027-01-29T05:54:37Z",
    "duration_h": 284.125,
    "duration_text": "11 d 20 h 8 min",
    "starts_in_h": 177.785,
    "open_at_window_start": false,
    "open_at_window_end": false
   }
  ]
 },
 "metrics": {
  "sunlight_pct": 40.09,
  "sunlight_hours": 284.125,
  "longest_darkness_h": 246.824,
  "earth_visibility_pct": 100.0,
  "earth_visible_hours": 708.734,
  "longest_comms_gap_h": 0.0,
  "power_and_comms_pct": 40.09,
  "sun_elevation_deg_max": 10.375,
  "sun_elevation_deg_min": -9.751,
  "sun_elevation_deg_mean_when_lit": 7.839,
  "earth_elevation_deg_max": 16.285,
  "earth_elevation_deg_min": 2.733,
  "mean_vertical_panel_factor": 0.3969,
  "mean_horizontal_panel_factor": 0.0546,
  "vertical_panel_energy_kwh_m2": 393.794,
  "n_sunsets": 1,
  "n_earthsets": 0,
  "libration_lat_range_deg": [
   -6.775,
   6.851
  ],
  "libration_lon_range_deg": [
   -7.768,
   7.412
  ]
 },
 "data_sources": {
  "ephemeris_backend": "analytic",
  "ephemeris_source": "Analytic ephemeris: Meeus Astronomical Algorithms ch.25/47 (Sun/Moon), IAU WGCCRE 2009 lunar orientation (~ME frame)"
 },
 "limitations": [
  "Sun/Earth positions from the ephemeris backend (analytic Meeus model or SPICE DE440)",
  "sunlit / visible = disk centre above the horizon; disk_visible_fraction gives partial disks",
  "horizon from the DEM (360 azimuth bins, rays to 100 km) only where a DEM covers the site",
  "events shorter than one sampling interval can be missed",
  "power factors are geometry only: no panel efficiency, temperature or dust",
  "Geometric line of sight to the Earth's centre only. Actual radio communication also depends on antenna pointing and gain, link budget, ground-station coverage on Earth, relay satellites and the lander's own terrain mask; it is not modelled here."
 ]
}`;export{e as default};
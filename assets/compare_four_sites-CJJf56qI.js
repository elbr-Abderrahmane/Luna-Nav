var e=`{
 "status": "ok",
 "result_type": "ephemeris_calculation",
 "warnings": [],
 "n_scenarios": 4,
 "rows": [
  {
   "label": "Shackleton-de Gerlache connecting ridge @ 2027-01-10",
   "site": {
    "id": "connecting-ridge",
    "name": "Shackleton-de Gerlache connecting ridge",
    "category": "south_pole_candidate",
    "mission": null,
    "agency": null,
    "coord_quality": "approximate",
    "lat_deg": -89.45,
    "lon_deg": -137.3,
    "elevation_m": 1954.44
   },
   "start_utc": "2027-01-10T00:00:00Z",
   "method": "horizon_mask",
   "warnings": [],
   "sunlit_at_start": true,
   "sun_elevation_deg_at_start": 1.063,
   "earth_visible_at_start": false,
   "earth_elevation_deg_at_start": -1.636,
   "sun_countdown": {
    "next_event": "sunset",
    "next_event_utc": null,
    "time_remaining_h": null,
    "time_remaining_text": null,
    "beyond_window": true,
    "summary": "Sun stays up for the whole 29.5-day window"
   },
   "earth_countdown": {
    "next_event": "earthrise",
    "next_event_utc": "2027-01-10T21:36:48Z",
    "time_remaining_h": 21.613,
    "time_remaining_text": "21 h 37 min",
    "beyond_window": false,
    "summary": "Earthrise in 21 h 37 min"
   },
   "metrics": {
    "sunlight_pct": 100.0,
    "sunlight_hours": 708.734,
    "longest_darkness_h": 0.0,
    "earth_visibility_pct": 48.0,
    "earth_visible_hours": 340.222,
    "longest_comms_gap_h": 346.898,
    "power_and_comms_pct": 48.0,
    "sun_elevation_deg_max": 1.063,
    "sun_elevation_deg_min": 0.05,
    "sun_elevation_deg_mean_when_lit": 0.45,
    "earth_elevation_deg_max": 6.151,
    "earth_elevation_deg_min": -7.543,
    "mean_vertical_panel_factor": 1.0,
    "mean_horizontal_panel_factor": 0.0078,
    "vertical_panel_energy_kwh_m2": 995.503,
    "n_sunsets": 0,
    "n_earthsets": 1,
    "libration_lat_range_deg": [
     -6.775,
     6.851
    ],
    "libration_lon_range_deg": [
     -7.768,
     7.412
    ]
   },
   "windows": {
    "sunlit": [
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
    "earth_visible": [
     {
      "start_utc": "2027-01-10T21:36:48Z",
      "end_utc": "2027-01-23T15:29:18Z",
      "duration_h": 305.875,
      "duration_text": "12 d 17 h 52 min",
      "starts_in_h": 21.613,
      "open_at_window_start": false,
      "open_at_window_end": false
     },
     {
      "start_utc": "2027-02-07T02:23:12Z",
      "end_utc": "2027-02-08T12:44:03Z",
      "duration_h": 34.347,
      "duration_text": "1 d 10 h 21 min",
      "starts_in_h": 674.387,
      "open_at_window_start": false,
      "open_at_window_end": true
     }
    ],
    "power_and_comms": [
     {
      "start_utc": "2027-01-10T21:36:48Z",
      "end_utc": "2027-01-23T15:29:18Z",
      "duration_h": 305.875,
      "duration_text": "12 d 17 h 52 min",
      "starts_in_h": 21.613,
      "open_at_window_start": false,
      "open_at_window_end": false
     },
     {
      "start_utc": "2027-02-07T02:23:12Z",
      "end_utc": "2027-02-08T12:44:03Z",
      "duration_h": 34.347,
      "duration_text": "1 d 10 h 21 min",
      "starts_in_h": 674.387,
      "open_at_window_start": false,
      "open_at_window_end": true
     }
    ]
   }
  },
  {
   "label": "Malapert Massif (Artemis III candidate region) @ 2027-01-10",
   "site": {
    "id": "artemis-malapert-massif",
    "name": "Malapert Massif (Artemis III candidate region)",
    "category": "artemis",
    "mission": "Artemis III",
    "agency": "NASA",
    "coord_quality": "approximate",
    "lat_deg": -85.95,
    "lon_deg": 2.9,
    "elevation_m": 4988.75
   },
   "start_utc": "2027-01-10T00:00:00Z",
   "method": "horizon_mask",
   "warnings": [],
   "sunlit_at_start": false,
   "sun_elevation_deg_at_start": -2.66,
   "earth_visible_at_start": true,
   "earth_elevation_deg_at_start": 2.774,
   "sun_countdown": {
    "next_event": "sunrise",
    "next_event_utc": "2027-01-12T13:51:20Z",
    "time_remaining_h": 61.855,
    "time_remaining_text": "2 d 13 h 51 min",
    "beyond_window": false,
    "summary": "Sunrise in 2 d 13 h 51 min"
   },
   "earth_countdown": {
    "next_event": "earthset",
    "next_event_utc": null,
    "time_remaining_h": null,
    "time_remaining_text": null,
    "beyond_window": true,
    "summary": "Earth stays up for the whole 29.5-day window"
   },
   "metrics": {
    "sunlight_pct": 53.27,
    "sunlight_hours": 377.547,
    "longest_darkness_h": 269.332,
    "earth_visibility_pct": 100.0,
    "earth_visible_hours": 708.734,
    "longest_comms_gap_h": 0.0,
    "power_and_comms_pct": 53.27,
    "sun_elevation_deg_max": 4.562,
    "sun_elevation_deg_min": -3.929,
    "sun_elevation_deg_mean_when_lit": 2.783,
    "earth_elevation_deg_max": 10.503,
    "earth_elevation_deg_min": -3.059,
    "mean_vertical_panel_factor": 0.5318,
    "mean_horizontal_panel_factor": 0.0264,
    "vertical_panel_energy_kwh_m2": 528.589,
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
   "windows": {
    "sunlit": [
     {
      "start_utc": "2027-01-12T13:51:20Z",
      "end_utc": "2027-01-28T07:24:08Z",
      "duration_h": 377.547,
      "duration_text": "15 d 17 h 33 min",
      "starts_in_h": 61.855,
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
      "start_utc": "2027-01-12T13:51:20Z",
      "end_utc": "2027-01-28T07:24:08Z",
      "duration_h": 377.547,
      "duration_text": "15 d 17 h 33 min",
      "starts_in_h": 61.855,
      "open_at_window_start": false,
      "open_at_window_end": false
     }
    ]
   }
  },
  {
   "label": "IM-1 Odysseus (Malapert A area) @ 2027-01-10",
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
   "start_utc": "2027-01-10T00:00:00Z",
   "method": "horizon_mask",
   "warnings": [],
   "sunlit_at_start": false,
   "sun_elevation_deg_at_start": -7.844,
   "earth_visible_at_start": true,
   "earth_elevation_deg_at_start": 8.587,
   "sun_countdown": {
    "next_event": "sunrise",
    "next_event_utc": "2027-01-17T09:47:07Z",
    "time_remaining_h": 177.785,
    "time_remaining_text": "7 d 9 h 47 min",
    "beyond_window": false,
    "summary": "Sunrise in 7 d 9 h 47 min"
   },
   "earth_countdown": {
    "next_event": "earthset",
    "next_event_utc": null,
    "time_remaining_h": null,
    "time_remaining_text": null,
    "beyond_window": true,
    "summary": "Earth stays up for the whole 29.5-day window"
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
    "sun_elevation_deg_mean_when_lit": 7.842,
    "earth_elevation_deg_max": 16.285,
    "earth_elevation_deg_min": 2.733,
    "mean_vertical_panel_factor": 0.3968,
    "mean_horizontal_panel_factor": 0.0546,
    "vertical_panel_energy_kwh_m2": 393.781,
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
   }
  },
  {
   "label": "Apollo 11 (Tranquility Base) @ 2027-01-10",
   "site": {
    "id": "apollo-11",
    "name": "Apollo 11 (Tranquility Base)",
    "category": "apollo",
    "mission": "Apollo 11",
    "agency": "NASA",
    "coord_quality": "landed",
    "lat_deg": 0.674,
    "lon_deg": 23.473,
    "elevation_m": 0.0
   },
   "start_utc": "2027-01-10T00:00:00Z",
   "method": "smooth_sphere",
   "warnings": [
    "terrain horizon unavailable here (site outside DEM coverage): smooth-sphere horizon, local shadows ignored"
   ],
   "sunlit_at_start": false,
   "sun_elevation_deg_at_start": -40.019,
   "earth_visible_at_start": true,
   "earth_elevation_deg_at_start": 63.235,
   "sun_countdown": {
    "next_event": "sunrise",
    "next_event_utc": "2027-01-13T06:51:48Z",
    "time_remaining_h": 78.863,
    "time_remaining_text": "3 d 6 h 52 min",
    "beyond_window": false,
    "summary": "Sunrise in 3 d 6 h 52 min"
   },
   "earth_countdown": {
    "next_event": "earthset",
    "next_event_utc": null,
    "time_remaining_h": null,
    "time_remaining_text": null,
    "beyond_window": true,
    "summary": "Earth stays up for the whole 29.5-day window"
   },
   "metrics": {
    "sunlight_pct": 50.2,
    "sunlight_hours": 355.812,
    "longest_darkness_h": 274.058,
    "earth_visibility_pct": 100.0,
    "earth_visible_hours": 708.734,
    "longest_comms_gap_h": 0.0,
    "power_and_comms_pct": 50.2,
    "sun_elevation_deg_max": 88.744,
    "sun_elevation_deg_min": -89.482,
    "sun_elevation_deg_mean_when_lit": 44.956,
    "earth_elevation_deg_max": 73.168,
    "earth_elevation_deg_min": 57.964,
    "mean_vertical_panel_factor": 0.3198,
    "mean_horizontal_panel_factor": 0.3197,
    "vertical_panel_energy_kwh_m2": 317.988,
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
   "windows": {
    "sunlit": [
     {
      "start_utc": "2027-01-13T06:51:48Z",
      "end_utc": "2027-01-28T02:40:33Z",
      "duration_h": 355.812,
      "duration_text": "14 d 19 h 49 min",
      "starts_in_h": 78.863,
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
      "start_utc": "2027-01-13T06:51:48Z",
      "end_utc": "2027-01-28T02:40:33Z",
      "duration_h": 355.812,
      "duration_text": "14 d 19 h 49 min",
      "starts_in_h": 78.863,
      "open_at_window_start": false,
      "open_at_window_end": false
     }
    ]
   }
  }
 ],
 "best": {
  "sunlight_pct": {
   "label": "Shackleton-de Gerlache connecting ridge @ 2027-01-10",
   "value": 100.0,
   "direction": "higher_is_better"
  },
  "longest_darkness_h": {
   "label": "Shackleton-de Gerlache connecting ridge @ 2027-01-10",
   "value": 0.0,
   "direction": "lower_is_better"
  },
  "earth_visibility_pct": {
   "label": "Malapert Massif (Artemis III candidate region) @ 2027-01-10",
   "value": 100.0,
   "direction": "higher_is_better"
  },
  "longest_comms_gap_h": {
   "label": "Apollo 11 (Tranquility Base) @ 2027-01-10",
   "value": 0.0,
   "direction": "lower_is_better"
  },
  "power_and_comms_pct": {
   "label": "Malapert Massif (Artemis III candidate region) @ 2027-01-10",
   "value": 53.27,
   "direction": "higher_is_better"
  },
  "vertical_panel_energy_kwh_m2": {
   "label": "Shackleton-de Gerlache connecting ridge @ 2027-01-10",
   "value": 995.503,
   "direction": "higher_is_better"
  },
  "sun_elevation_deg_max": {
   "label": "Apollo 11 (Tranquility Base) @ 2027-01-10",
   "value": 88.744,
   "direction": "higher_is_better"
  }
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
# How to read a verdict

Each scenario (a site and a landing date) gets one of three verdicts.

| Verdict | Meaning |
|---|---|
| **Viable** | Conditions are broadly favorable for power and direct-to-Earth communication. |
| **Marginal** | Workable, but with constraints that need a plan (bigger battery, a relay satellite, another date). |
| **Not viable** | At least one condition is unfavorable under our criteria. |

## The rule (default thresholds)

- **Not viable** if the longest night is over 100 h, or sunlight is under 30 %, or Earth visibility is under 20 %.
- **Viable** if sunlight is at least 60 %, the longest night is at most 50 h, Earth visibility is at least 50 % and the longest comms gap is at most 72 h.
- **Marginal** in every other case.

The "not viable" tests come first. The numbers used for each verdict are shown in the interface.

## Assumptions

We assume a **solar-powered lander with about four days of battery and direct-to-Earth communication**. These thresholds are our team's assumptions, **not NASA rules**.

## Limits

- Only the geometry of Sun and Earth is used: no terrain hazards, slopes, thermal limits, landing accuracy or radio link budget.
- Metrics are computed over the analysis window, so a shorter mission can change the verdict.
- Sites outside the terrain data use a smooth-sphere horizon, so local shadows are ignored.

A LunaNav verdict is an **indicative assessment**, not a certification of landing safety.

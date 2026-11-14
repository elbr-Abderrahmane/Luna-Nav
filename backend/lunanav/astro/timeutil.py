"""Time helpers: UTC parsing/formatting and Julian dates (README §6.1, §6.4)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np

# TT - UTC = (TAI - UTC) + 32.184 s. TAI - UTC has been 37 s since 2017-01-01 and no new leap
# second is scheduled; good enough for an analytic model (the SPICE backend uses the real LSK).
TT_MINUS_UTC_S = 37.0 + 32.184
J2000_JD = 2451545.0
_UNIX_EPOCH_JD = 2440587.5


def to_utc(t: datetime | str) -> datetime:
    """Return an aware UTC datetime. Naive datetimes are taken as UTC; strings may end in Z."""
    if isinstance(t, str):
        t = datetime.fromisoformat(t.replace("Z", "+00:00"))
    if t.tzinfo is None:
        return t.replace(tzinfo=UTC)
    return t.astimezone(UTC)


def fmt_utc(t: datetime) -> str:
    """ISO-8601 UTC string ending in Z, whole seconds: 2027-03-14T12:00:00Z."""
    t = to_utc(t)
    if t.microsecond >= 500_000:
        t = t + timedelta(microseconds=1_000_000 - t.microsecond)
    return t.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def time_grid(start: datetime, hours: float, step_h: float) -> list[datetime]:
    """Inclusive grid start, start+step, ..., start+hours."""
    n = round(hours / step_h)
    start = to_utc(start)
    return [start + timedelta(hours=k * step_h) for k in range(n + 1)]


def jd_tt(times: datetime | list[datetime]) -> np.ndarray:
    """Julian date (TT) for one or many UTC datetimes, as a float64 array."""
    if isinstance(times, datetime):
        times = [times]
    unix = np.array([to_utc(t).timestamp() for t in times], dtype=float)
    return _UNIX_EPOCH_JD + (unix + TT_MINUS_UTC_S) / 86400.0

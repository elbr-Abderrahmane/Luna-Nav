"""Ephemeris backends.

Every backend answers three questions for an array of UTC times:

* ``moon_eci_km(times)``  -> (n, 3) Moon centre w.r.t. Earth centre, J2000, km
* ``sun_eci_km(times)``   -> (n, 3) Sun centre w.r.t. Earth centre, J2000, km
* ``j2000_to_moon_me(times)`` -> (n, 3, 3) rotation, v_ME = R @ v_J2000

Two implementations:

* ``AnalyticEphemeris`` (default, no files needed): Meeus, *Astronomical Algorithms* 2nd ed.,
  ch. 47 (ELP-2000/82 truncated, ~10" in longitude) for the Moon and ch. 25 (low precision,
  ~0.01 deg) for the Sun, precessed to J2000; lunar orientation from the IAU WGCCRE 2009 model
  (Archinal et al. 2011), which approximates the Mean-Earth/Polar-axis frame to well under 0.01 deg.
* ``SpiceEphemeris``: NAIF kernels via spiceypy (DE440 + lunar PA/ME frame kernels), used when
  ``scripts/astro/fetch_kernels.py`` has been run. Select with ``LUNANAV_EPHEMERIS=auto|analytic|spice``.
"""

from __future__ import annotations

import os
import threading
import warnings
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np

from .timeutil import J2000_JD, jd_tt, to_utc

_SPICE_LOCK = threading.RLock()

AU_KM = 149_597_870.7
OBLIQUITY_J2000_DEG = 23.4392911
_D2R = np.pi / 180.0

# ---------------------------------------------------------------------------------------------
# Meeus table 47.A: D, M, M', F, Sigma_l (1e-6 deg), Sigma_r (1e-3 km)
_MOON_LR = np.array([
    (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111),
    (2, 0, 0, 0, 658314, -2955968), (0, 0, 2, 0, 213618, -569925),
    (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
    (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138),
    (2, 0, 1, 0, 53322, -170733), (2, -1, 0, 0, 45758, -204586),
    (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321),
    (0, 0, 1, 2, -12528, 0), (0, 0, 1, -2, 10980, 79661),
    (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
    (4, 0, -2, 0, 8548, -21636), (2, 1, -1, 0, -7888, 24208),
    (2, 1, 0, 0, -6766, 30824), (1, 0, -1, 0, -5163, -8379),
    (1, 1, 0, 0, 4987, -16675), (2, -1, 1, 0, 4036, -12831),
    (2, 0, 2, 0, 3994, -10445), (4, 0, 0, 0, 3861, -11650),
    (2, 0, -3, 0, 3665, 14403), (0, 1, -2, 0, -2689, -7003),
    (2, 0, -1, 2, -2602, 0), (2, -1, -2, 0, 2390, 10056),
    (1, 0, 1, 0, -2348, 6322), (2, -2, 0, 0, 2236, -9884),
    (0, 1, 2, 0, -2120, 5751), (0, 2, 0, 0, -2069, 0),
    (2, -2, -1, 0, 2048, -4950), (2, 0, 1, -2, -1773, 4130),
    (2, 0, 0, 2, -1595, 0), (4, -1, -1, 0, 1215, -3958),
    (0, 0, 2, 2, -1110, 0), (3, 0, -1, 0, -892, 3258),
    (2, 1, 1, 0, -810, 2616), (4, -1, -2, 0, 759, -1897),
    (0, 2, -1, 0, -713, -2117), (2, 2, -1, 0, -700, 2354),
    (2, 1, -2, 0, 691, 0), (2, -1, 0, -2, 596, 0),
    (4, 0, 1, 0, 549, -1423), (0, 0, 4, 0, 537, -1117),
    (4, -1, 0, 0, 520, -1571), (1, 0, -2, 0, -487, -1739),
    (2, 1, 0, -2, -399, 0), (0, 0, 2, -2, -381, -4421),
    (1, 1, 1, 0, 351, 0), (3, 0, -2, 0, -340, 0),
    (4, 0, -3, 0, 330, 0), (2, -1, 2, 0, 327, 0),
    (0, 2, 1, 0, -323, 1165), (1, 1, -1, 0, 299, 0),
    (2, 0, 3, 0, 294, 0), (2, 0, -1, -2, 0, 8752),
], dtype=float)

# Meeus table 47.B: D, M, M', F, Sigma_b (1e-6 deg)
_MOON_B = np.array([
    (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693),
    (2, 0, 0, -1, 173237), (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271),
    (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198), (2, 0, 1, -1, 9266),
    (0, 0, 2, -1, 8822), (2, -1, 0, -1, 8216), (2, 0, -2, -1, 4324),
    (2, 0, 1, 1, 4200), (2, 1, 0, -1, -3359), (2, -1, -1, 1, 2463),
    (2, -1, 0, 1, 2211), (2, -1, -1, -1, 2065), (0, 1, -1, -1, -1870),
    (4, 0, -1, -1, 1828), (0, 1, 0, 1, -1794), (0, 0, 0, 3, -1749),
    (0, 1, -1, 1, -1565), (1, 0, 0, 1, -1491), (0, 1, 1, 1, -1475),
    (0, 1, 1, -1, -1410), (0, 1, 0, -1, -1344), (1, 0, 0, -1, -1335),
    (0, 0, 3, 1, 1107), (4, 0, 0, -1, 1021), (4, 0, -1, 1, 833),
    (0, 0, 1, -3, 777), (4, 0, -2, 1, 671), (2, 0, 0, -3, 607),
    (2, 0, 2, -1, 596), (2, -1, 1, -1, 491), (2, 0, -2, 1, -451),
    (0, 0, 3, -1, 439), (2, 0, 2, 1, 422), (2, 0, -3, -1, 421),
    (2, 1, -1, 1, -366), (2, 1, 0, 1, -351), (4, 0, 0, 1, 331),
    (2, -1, 1, 1, 315), (2, -2, 0, -1, 302), (0, 0, 1, 3, -283),
    (2, 1, 1, -1, -229), (1, 1, 0, -1, 223), (1, 1, 0, 1, 223),
    (0, 1, -2, -1, -220), (2, 1, -1, -1, -220), (1, 0, 1, 1, -185),
    (2, -1, -2, -1, 181), (0, 1, 2, 1, -177), (4, 0, -2, -1, 176),
    (4, -1, -1, -1, 166), (1, 0, 1, -1, -164), (4, 0, 1, -1, 132),
    (1, 0, -1, -1, -119), (4, -1, 0, -1, 115), (2, -2, 0, 1, 107),
], dtype=float)


def _precession_lon_deg(T: np.ndarray) -> np.ndarray:
    """General precession in longitude since J2000 (deg); of-date -> J2000 subtracts this."""
    return (5029.0966 * T + 1.11113 * T**2) / 3600.0


def _ecl_to_eq_j2000(lon_deg, lat_deg, dist_km) -> np.ndarray:
    lon, lat = lon_deg * _D2R, lat_deg * _D2R
    x = dist_km * np.cos(lat) * np.cos(lon)
    y = dist_km * np.cos(lat) * np.sin(lon)
    z = dist_km * np.sin(lat)
    eps = OBLIQUITY_J2000_DEG * _D2R
    return np.stack([x, y * np.cos(eps) - z * np.sin(eps), y * np.sin(eps) + z * np.cos(eps)], -1)


def moon_ecliptic_of_date(jde: np.ndarray):
    """Geometric Moon (lon_deg, lat_deg, dist_km), mean ecliptic & equinox of date. Meeus ch. 47."""
    T = (np.asarray(jde, float) - J2000_JD) / 36525.0
    Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T**2 + T**3 / 538841 - T**4 / 65194000
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T**2 + T**3 / 545868 - T**4 / 113065000
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T**2 + T**3 / 24490000
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T**2 + T**3 / 69699 - T**4 / 14712000
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T**2 - T**3 / 3526000 + T**4 / 863310000
    A1 = 119.75 + 131.849 * T
    A2 = 53.09 + 479264.290 * T
    A3 = 313.45 + 481266.484 * T
    E = 1 - 0.002516 * T - 0.0000074 * T**2

    args = np.stack([D, M, Mp, F], -1) * _D2R  # (n, 4)

    def series(tab, coef_col, trig):
        ang = args @ tab[:, :4].T  # (n, k)
        e_fac = E[:, None] ** np.abs(tab[:, 1])[None, :]
        return (tab[:, coef_col][None, :] * e_fac * trig(ang)).sum(-1)

    sl = series(_MOON_LR, 4, np.sin)
    sr = series(_MOON_LR, 5, np.cos)
    sb = series(_MOON_B, 4, np.sin)
    r = _D2R
    sl += 3958 * np.sin(A1 * r) + 1962 * np.sin((Lp - F) * r) + 318 * np.sin(A2 * r)
    sb += (-2235 * np.sin(Lp * r) + 382 * np.sin(A3 * r) + 175 * np.sin((A1 - F) * r)
           + 175 * np.sin((A1 + F) * r) + 127 * np.sin((Lp - Mp) * r) - 115 * np.sin((Lp + Mp) * r))
    lon = np.mod(Lp + sl / 1e6, 360.0)
    lat = sb / 1e6
    dist = 385000.56 + sr / 1000.0
    return lon, lat, dist


def sun_ecliptic_of_date(jde: np.ndarray):
    """Geometric Sun (lon_deg, lat_deg=0, dist_km), mean equinox of date. Meeus ch. 25."""
    T = (np.asarray(jde, float) - J2000_JD) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T**2
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T**2) * _D2R
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T**2
    C = ((1.914602 - 0.004817 * T - 0.000014 * T**2) * np.sin(M)
         + (0.019993 - 0.000101 * T) * np.sin(2 * M) + 0.000289 * np.sin(3 * M))
    nu = M + C * _D2R
    R_au = 1.000001018 * (1 - e**2) / (1 + e * np.cos(nu))
    return np.mod(L0 + C, 360.0), np.zeros_like(T), R_au * AU_KM


def iau_moon_orientation(jde: np.ndarray):
    """IAU 2009 lunar pole (alpha0, delta0) and prime meridian W, degrees (Archinal et al. 2011)."""
    d = np.asarray(jde, float) - J2000_JD
    T = d / 36525.0
    E = np.radians(np.stack([
        125.045 - 0.0529921 * d, 250.089 - 0.1059842 * d, 260.008 + 13.0120009 * d,
        176.625 + 13.3407154 * d, 357.529 + 0.9856003 * d, 311.589 + 26.4057084 * d,
        134.963 + 13.0649930 * d, 276.617 + 0.3287146 * d, 34.226 + 1.7484877 * d,
        15.134 - 0.1589763 * d, 119.743 + 0.0036096 * d, 239.961 + 0.1643573 * d,
        25.053 + 12.9590088 * d,
    ]))
    s, c = np.sin(E), np.cos(E)
    a0 = (269.9949 + 0.0031 * T - 3.8787 * s[0] - 0.1204 * s[1] + 0.0700 * s[2] - 0.0172 * s[3]
          + 0.0072 * s[5] - 0.0052 * s[9] + 0.0043 * s[12])
    d0 = (66.5392 + 0.0130 * T + 1.5419 * c[0] + 0.0239 * c[1] - 0.0278 * c[2] + 0.0068 * c[3]
          - 0.0029 * c[5] + 0.0009 * c[6] + 0.0008 * c[9] - 0.0009 * c[12])
    W = (38.3213 + 13.17635815 * d - 1.4e-12 * d**2 + 3.5610 * s[0] + 0.1208 * s[1]
         - 0.0642 * s[2] + 0.0158 * s[3] + 0.0252 * s[4] - 0.0066 * s[5] - 0.0047 * s[6]
         - 0.0046 * s[7] + 0.0028 * s[8] + 0.0052 * s[9] + 0.0040 * s[10] + 0.0019 * s[11]
         - 0.0044 * s[12])
    return a0, d0, np.mod(W, 360.0)


def _rz(a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([c, s, z], -1), np.stack([-s, c, z], -1), np.stack([z, z, o], -1)], -2)


def _rx(a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([o, z, z], -1), np.stack([z, c, s], -1), np.stack([z, -s, c], -1)], -2)


class AnalyticEphemeris:
    name = "analytic"
    source = ("Analytic ephemeris: Meeus Astronomical Algorithms ch.25/47 (Sun/Moon), "
              "IAU WGCCRE 2009 lunar orientation (~ME frame)")

    def moon_eci_km(self, times: list[datetime]) -> np.ndarray:
        jde = jd_tt(times)
        lon, lat, dist = moon_ecliptic_of_date(jde)
        lon = lon - _precession_lon_deg((jde - J2000_JD) / 36525.0)
        return _ecl_to_eq_j2000(lon, lat, dist)

    def sun_eci_km(self, times: list[datetime]) -> np.ndarray:
        jde = jd_tt(times)
        lon, lat, dist = sun_ecliptic_of_date(jde)
        lon = lon - _precession_lon_deg((jde - J2000_JD) / 36525.0)
        return _ecl_to_eq_j2000(lon, lat, dist)

    def j2000_to_moon_me(self, times: list[datetime]) -> np.ndarray:
        a0, d0, W = iau_moon_orientation(jd_tt(times))
        return _rz(np.radians(W)) @ _rx(np.radians(90.0 - d0)) @ _rz(np.radians(90.0 + a0))


# ---------------------------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
KERNEL_DIR = Path(os.environ.get("LUNANAV_KERNEL_DIR", REPO_ROOT / "data" / "raw" / "kernels"))
METAKERNEL = KERNEL_DIR / "lunanav.tm"
# Kernel files loaded in this order (newest match of each pattern), see fetch_kernels.py
KERNEL_PATTERNS = ("naif*.tls", "de440s.bsp", "moon_pa_de440_*.bpc", "moon_de440_*.tf")
# Why the last `auto` selection fell back to the analytic model (None = it did not)
FALLBACK_REASON: str | None = None


def kernel_dir_candidates() -> list[Path]:
    """Where to look for kernels, first match wins. Independent of the working directory
    except for the last two entries, which only help when the package is installed elsewhere."""
    out = []
    if os.environ.get("LUNANAV_KERNEL_DIR"):
        out.append(Path(os.environ["LUNANAV_KERNEL_DIR"]))
    out.append(REPO_ROOT / "data" / "raw" / "kernels")
    cwd = Path.cwd()
    out += [cwd / "data" / "raw" / "kernels", cwd.parent / "data" / "raw" / "kernels"]
    unique: list[Path] = []
    for p in out:
        if p.resolve() not in unique:
            unique.append(p.resolve())
    return unique


def find_kernels() -> tuple[Path | None, list[Path], str]:
    """(kernel dir, kernel files in load order, message). Files empty = not found."""
    tried = []
    for d in kernel_dir_candidates():
        d = d.resolve()
        files = [max(d.glob(p), default=None) for p in KERNEL_PATTERNS]
        if all(files):
            return d, files, f"kernels found in {d}"
        missing = [p for p, f in zip(KERNEL_PATTERNS, files, strict=True) if f is None]
        tried.append(f"{d} (missing {', '.join(missing)})")
    return None, [], "no complete kernel set; looked in: " + "; ".join(tried)


class SpiceEphemeris:
    name = "spice"

    def __init__(self, kernel_files: list[Path] | None = None):
        import spiceypy as sp  # optional dependency

        if kernel_files is None:
            _, kernel_files, msg = find_kernels()
            if not kernel_files:
                raise FileNotFoundError(msg + ". Run scripts/astro/fetch_kernels.py")
        self._sp = sp
        # Load each file by absolute path (no metakernel): avoids PATH_VALUES quirks and
        # SPICE's 80-character string limit on long Windows paths.
        with _SPICE_LOCK:
            for f in kernel_files:
                sp.furnsh(str(Path(f).resolve()))
        self.kernel_files = [Path(f) for f in kernel_files]
        self.source = "NAIF SPICE kernels: " + ", ".join(f.name for f in self.kernel_files)

    def _et(self, times):
        with _SPICE_LOCK:
            return [self._sp.str2et(to_utc(t).strftime("%Y-%m-%dT%H:%M:%S.%f")) for t in times]

    def moon_eci_km(self, times):
        with _SPICE_LOCK:
            ets = self._et(times)
            return np.array([self._sp.spkpos("MOON", et, "J2000", "NONE", "EARTH")[0]
                             for et in ets])

    def sun_eci_km(self, times):
        with _SPICE_LOCK:
            ets = self._et(times)
            return np.array([self._sp.spkpos("SUN", et, "J2000", "NONE", "EARTH")[0]
                             for et in ets])

    def j2000_to_moon_me(self, times):
        with _SPICE_LOCK:
            ets = self._et(times)
            return np.array([self._sp.pxform("J2000", "MOON_ME", et) for et in ets])


@lru_cache(maxsize=1)
def get_ephemeris():
    """Pick the backend: env LUNANAV_EPHEMERIS = auto (default) | analytic | spice.

    auto = SPICE when a complete kernel set is found (see `kernel_dir_candidates`), else the
    analytic model. The reason for a fallback is kept in `FALLBACK_REASON` and issued as a
    warning, never swallowed silently. `spice` raises if SPICE cannot be loaded.
    """
    global FALLBACK_REASON
    FALLBACK_REASON = None
    choice = os.environ.get("LUNANAV_EPHEMERIS", "auto").lower()
    if choice == "analytic":
        return AnalyticEphemeris()
    try:
        return SpiceEphemeris()
    except Exception as exc:
        if choice == "spice":
            raise
        FALLBACK_REASON = f"{type(exc).__name__}: {exc}"
        warnings.warn(f"SPICE not used, analytic ephemeris instead ({FALLBACK_REASON})",
                      RuntimeWarning, stacklevel=2)
    return AnalyticEphemeris()

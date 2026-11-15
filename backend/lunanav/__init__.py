"""LunaNav scientific domain package.

Subpackages:
- `lunanav.coords`   (P2): Lunar ME coordinate normalization and south-polar stereographic projection
- `lunanav.terrain`  (P2): LOLA DEM access, coverage checks, heightmaps, and local slope/roughness
- `lunanav.astro`    (P3): Ephemeris, terrain horizon masks, illumination, 26-site catalog, scenarios
- `lunanav.decision` (P4): Viability verdicts, plain-language explanations, WSM/TOPSIS ranking & sensitivity
"""

from __future__ import annotations

__version__ = "1.0.0"

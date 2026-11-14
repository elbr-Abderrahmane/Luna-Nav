import os
import sys
from pathlib import Path

import pytest

# module-scoped fixtures run before the autouse fixture below: pin the model for them too
os.environ["LUNANAV_EPHEMERIS"] = "analytic"
os.environ["LUNANAV_DEM"] = "off"  # tests never pick up a downloaded LOLA DEM unless asked

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("LUNANAV_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("LUNANAV_EPHEMERIS", "analytic")
    from lunanav.astro.ephemeris import get_ephemeris

    get_ephemeris.cache_clear()
    yield
    get_ephemeris.cache_clear()

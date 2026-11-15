import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

MOCK = BACKEND.parent / "mock_data" / "astro"


def load_mock(name):
    path = MOCK / name
    if not path.exists():
        pytest.skip(f"{name} not found in mock_data/astro")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def good():
    """Métriques qui satisfont les 4 conditions « viable »."""
    return {"sunlight_pct": 80, "longest_darkness_h": 20,
            "earth_visibility_pct": 70, "longest_comms_gap_h": 30}


@pytest.fixture
def compare_rows():
    return load_mock("compare_four_sites.json")["rows"]


@pytest.fixture
def sweep_rows():
    return load_mock("date_sweep_connecting-ridge.json")["rows"]

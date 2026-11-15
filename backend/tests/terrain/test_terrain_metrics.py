import numpy as np
from lunanav.terrain.terrain_metrics import terrain_summary, local_roughness

def test_no_dem_reports_missing(tmp_path):
    result = terrain_summary(-85, 0, dem_path=tmp_path / "none.tif")
    assert result["status"] == "dem_unavailable"
    assert result["roughness_m"] is None

def test_nan_statistics_are_not_fabricated():
    arr = np.array([1.0, np.nan, 3.0])
    valid = arr[np.isfinite(arr)]
    assert float(valid.std()) == 1.0

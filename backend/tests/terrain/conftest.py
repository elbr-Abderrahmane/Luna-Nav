from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
import math

@pytest.fixture
def tiny_dem(tmp_path: Path) -> Path:
    """Small synthetic polar-projection raster; test fixture only, not NASA data."""
    path = tmp_path / "synthetic_test_dem.tif"
    data = np.arange(100, dtype="float32").reshape(10, 10)
    y_center = 2 * 1_737_400.0 * math.tan(math.pi / 4 + math.radians(-85) / 2)
    data[0, 0] = -9999
    with rasterio.open(
        path, "w", driver="GTiff", height=10, width=10, count=1,
        dtype="float32", crs=None, transform=from_origin(-400, y_center + 400, 80, 80),
        nodata=-9999,
    ) as dst:
        dst.write(data, 1)
    return path

"""LolaDEM reader on a tiny synthetic GeoTIFF with the real product's layout."""

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")

from affine import Affine

from lunanav.astro._contracts import LatLon
from lunanav.astro.lola_dem import NODATA, LolaDEM, stereo
from lunanav.astro.scenarios import SiteModel

CRS = "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"
RES = 400.0
HALF = 60_000.0


@pytest.fixture()
def dem(tmp_path):
    n = int(2 * HALF / RES)
    xs = -HALF + (np.arange(n) + 0.5) * RES
    ys = HALF - (np.arange(n) + 0.5) * RES
    grid = (0.01 * xs[None, :] + 0.0 * ys[:, None]).astype(np.float32)   # tilted plane
    grid[0, 0] = np.nan
    path = tmp_path / "LDEM_TEST.TIF"
    with rasterio.open(path, "w", driver="GTiff", width=n, height=n, count=1, dtype="float32",
                       crs=CRS, transform=Affine(RES, 0, -HALF, 0, -RES, HALF),
                       nodata=np.nan) as ds:
        ds.write(grid, 1)
    return LolaDEM(path)


def test_sample_elevation_matches_plane(dem):
    lat, lon = -89.5, 30.0
    x, _ = stereo(lat, lon)
    assert dem.sample_elevation(lat, lon) == pytest.approx(0.01 * x, abs=0.05)
    assert np.isnan(dem.sample_elevation(-80.0, 0.0))        # outside the file


def test_window_is_boundless_with_nodata(dem):
    grid, tr = dem.dem_window(LatLon(lat_deg=-89.0, lon_deg=90.0), 50_000)
    assert grid.dtype == np.float32 and grid.shape[0] == grid.shape[1]
    assert (grid == NODATA).any() and np.isfinite(grid).all()
    assert tr.a == RES and tr.e == -RES


def test_site_model_uses_it_and_falls_back_outside(dem):
    assert SiteModel(-89.8, 0.0, dem=dem).method == "horizon_mask"
    far = SiteModel(0.674, 23.473, dem=dem)
    assert far.method == "smooth_sphere" and far.warnings

import math
import pytest
from lunanav.coords import latlon_to_xy, xy_to_latlon, normalize_latlon, is_nominal_dem_latitude

@pytest.mark.parametrize("lat,lon", [(-80, 0), (-85, 45), (-89.5, -120), (-80, 179.9)])
def test_round_trip(lat, lon):
    x, y = latlon_to_xy(lat, lon)
    lat2, lon2 = xy_to_latlon(x, y)
    assert lat2 == pytest.approx(lat, abs=1e-10)
    assert ((lon2-lon+180) % 360)-180 == pytest.approx(0, abs=1e-10)

def test_south_pole():
    assert latlon_to_xy(-90, 25) == (0.0, 0.0)
    assert xy_to_latlon(0, 0) == (-90.0, 0.0)

def test_east_positive_longitude():
    x_east, y_east = latlon_to_xy(-85, 90)
    x_west, y_west = latlon_to_xy(-85, -90)
    assert x_east > 0 and x_west < 0
    assert y_east == pytest.approx(y_west)

def test_longitude_normalization():
    assert normalize_latlon(-85, 190) == (-85.0, -170.0)
    assert normalize_latlon(-85, 360) == (-85.0, 0.0)

def test_invalid_latitude():
    with pytest.raises(ValueError):
        latlon_to_xy(-91, 0)

def test_nominal_envelope():
    assert is_nominal_dem_latitude(-80)
    assert is_nominal_dem_latitude(-90)
    assert not is_nominal_dem_latitude(-79.9)

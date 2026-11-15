from lunanav.terrain.dem import DEMReader, inspect_dem, site_coverage, sample_elevation

def test_missing_dem(tmp_path):
    missing = tmp_path / "missing.tif"
    assert inspect_dem(missing)["status"] == "dem_unavailable"
    assert site_coverage(-85, 0, missing)["status"] == "dem_unavailable"

def test_metadata_and_sampling(tiny_dem):
    with DEMReader(tiny_dem) as reader:
        meta = reader.metadata()
        assert meta["width_px"] == 10 and meta["height_px"] == 10
        assert meta["band_count"] == 1
        assert meta["resolution_m"] == [80.0, 80.0]
    result = sample_elevation(-85, 0, tiny_dem)
    assert result["status"] in {"ok", "outside_raster_bounds"}
    assert result["elevation_m"] is None or isinstance(result["elevation_m"], float)

def test_outside_nominal_coverage(tiny_dem):
    assert site_coverage(-79, 0, tiny_dem)["status"] == "outside_nominal_coverage"

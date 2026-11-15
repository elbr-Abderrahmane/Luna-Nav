import json
import pytest
from lunanav.terrain.heightmap import extract_heightmap

def test_invalid_radius(tiny_dem):
    with pytest.raises(ValueError):
        extract_heightmap(-85, 0, 0, tiny_dem)

def test_heightmap_json_safe(tiny_dem):
    result = extract_heightmap(-85, 0, 160, tiny_dem)
    json.dumps(result)
    assert "values_m" in result
    assert isinstance(result["rows"], int)

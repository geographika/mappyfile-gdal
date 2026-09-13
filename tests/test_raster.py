import pytest

from mappyfile_gdal.raster import (
    get_map_size,
    get_scale,
    process_raster,
)


@pytest.fixture
def raster_data():
    """Cut-down gdal raster info JSON, based on aaigrid/pixel_per_line.asc."""
    return {
        "description": "aaigrid/pixel_per_line.asc",
        "files": ["aaigrid/pixel_per_line.asc", "aaigrid\\pixel_per_line.prj"],
        "size": [15, 12],
        "cornerCoordinates": {
            "lowerLeft": [100000.0, 650000.0],
            "upperRight": [100750.0, 650600.0],
        },
        "bands": [
            {"band": 1, "minimum": 0.0, "maximum": 3450.0, "noDataValue": -99999.0}
        ],
        "stac": {"proj:epsg": None},
    }


def test_small_raster_is_upscaled_by_whole_number():
    # 15 x 12 needs a factor of 18 to reach the 256 minimum
    assert get_map_size(15, 12) == [270, 216]


def test_large_raster_keeps_aspect_ratio():
    assert get_map_size(10000, 2000) == [4096, 819]


def test_min_max_from_single_band(raster_data):
    assert get_scale(raster_data) == (0.0, 3450.0)


def test_equal_min_and_max_returns_none():
    # An empty raster can't be stretched
    assert get_scale({"bands": [{"minimum": 0.0, "maximum": 0.0}]}) is None


def test_process_raster(raster_data):
    m = {}
    process_raster(m, raster_data)

    assert m["size"] == [270, 216]
    assert m["extent"] == [100001.389, 650001.389, 100748.611, 650598.611]
    assert "projection" not in m  # no EPSG code in the JSON

    assert m["layers"] == [
        {
            "__type__": "layer",
            "name": "pixel_per_line",
            "type": "raster",
            "status": "on",
            "data": "aaigrid/pixel_per_line.asc",
            "processing": ["SCALE=0,3450", "NODATA=-99999.0"],
        }
    ]

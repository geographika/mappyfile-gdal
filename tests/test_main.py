import pytest

from mappyfile_gdal.main import dataset_type


def test_raster_only_driver():
    assert dataset_type({"driverShortName": "GTiff", "bands": []}) == "raster"


def test_vector_only_driver():
    assert dataset_type({"driverShortName": "ESRI Shapefile", "layers": []}) == "vector"


@pytest.mark.parametrize("key,expected", [("layers", "vector"), ("bands", "raster")])
def test_driver_supporting_both_uses_the_json_keys(key, expected):
    # GPKG is raster and vector, so only the JSON says which info this is
    assert dataset_type({"driverShortName": "GPKG", key: []}) == expected


def test_unknown_driver_without_keys_raises():
    with pytest.raises(ValueError):
        dataset_type({"driverShortName": "MADEUP"})

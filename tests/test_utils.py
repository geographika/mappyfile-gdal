from mappyfile_gdal.utils import get_projection, mapserver_extent


def test_extent_is_inset_by_half_a_pixel():
    # 100 units across 10 pixels = 10 per pixel, so inset by 5
    assert mapserver_extent(0, 0, 100, 100, [10, 10]) == [5.0, 5.0, 95.0, 95.0]


def test_non_square_pixels_use_their_own_offsets():
    # 10 units wide, 25 units tall
    assert mapserver_extent(0, 0, 100, 100, [10, 4]) == [5.0, 12.5, 95.0, 87.5]


def test_decimals_follow_the_pixel_size():
    # 2.7778 unit pixels round to 3 decimals
    assert mapserver_extent(100000, 650000, 100750, 650600, [270, 216]) == [
        100001.389,
        650001.389,
        100748.611,
        650598.611,
    ]


def test_small_pixels_keep_more_decimals():
    # A WGS84 raster with 0.0001 degree pixels needs 7 decimals
    assert mapserver_extent(-1, -1, 0, 0, [10000, 10000]) == [
        -0.99995,
        -0.99995,
        -5e-05,
        -5e-05,
    ]


def test_authority_and_code_are_formatted():
    assert get_projection({"id": {"authority": "EPSG", "code": 4326}}) == "EPSG:4326"


def test_ids_list_is_used_when_there_is_no_id():
    assert get_projection({"ids": [{"authority": "EPSG", "code": 3857}]}) == "EPSG:3857"


def test_crs_without_a_code_returns_none():
    # An unnamed CRS has PROJJSON but no identifier
    assert get_projection({"name": "unnamed"}) is None


def test_missing_projjson_returns_none():
    assert get_projection(None) is None


def test_non_epsg_authority_is_kept():
    # e.g. ESRI:54052, which has no EPSG equivalent
    assert get_projection({"id": {"authority": "ESRI", "code": 54052}}) == "ESRI:54052"

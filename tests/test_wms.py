import pytest

from mappyfile_gdal.wms import parse_wms_subdatasets, process_wms_catalog

SERVER = "https://demo.mapserver.org/cgi-bin/wms"


def subdataset(layer, bbox, version="1.3.0", crs="EPSG:4326", extra=""):
    return (
        f"WMS:{SERVER}?SERVICE=WMS&VERSION={version}&REQUEST=GetMap"
        f"&LAYERS={layer}&CRS={crs}&BBOX={bbox}{extra}"
    )


@pytest.fixture
def wms_data():
    """Cut-down gdal raster info JSON for a WMS capabilities catalog."""
    return {
        "driverShortName": "WMS",
        "bands": [],
        "metadata": {
            "SUBDATASETS": {
                "SUBDATASET_1_NAME": subdataset(
                    "bluemarble", "-90.0,-180.0,90.0,180.0"
                ),
                "SUBDATASET_1_DESC": "Blue Marble",
                "SUBDATASET_2_NAME": subdataset("cities", "-54.8,-178.2,78.9,179.4"),
                "SUBDATASET_2_DESC": "World cities",
            }
        },
    }


def test_wms_130_bbox_is_swapped_to_lon_lat(wms_data):
    # WMS 1.3.0 gives EPSG:4326 as lat/lon, MapServer wants lon/lat
    layers = parse_wms_subdatasets(wms_data)

    assert layers[0]["extent"] == [-180.0, -90.0, 180.0, 90.0]


def test_wms_111_bbox_is_left_alone(wms_data):
    wms_data["metadata"]["SUBDATASETS"]["SUBDATASET_1_NAME"] = subdataset(
        "bluemarble", "-180.0,-90.0,180.0,90.0", version="1.1.1"
    )
    layers = parse_wms_subdatasets(wms_data)

    assert layers[0]["extent"] == [-180.0, -90.0, 180.0, 90.0]


def test_getmap_params_are_stripped_from_the_connection(wms_data):
    layers = parse_wms_subdatasets(wms_data)

    assert layers[0]["connection"] == f"{SERVER}?"


def test_other_params_are_kept_in_the_connection(wms_data):
    wms_data["metadata"]["SUBDATASETS"]["SUBDATASET_1_NAME"] = subdataset(
        "bluemarble", "-90.0,-180.0,90.0,180.0", extra="&map=/etc/demo.map"
    )
    layers = parse_wms_subdatasets(wms_data)

    # note the key is upper-cased, since params are normalised on parsing
    assert layers[0]["connection"] == f"{SERVER}?MAP=%2Fetc%2Fdemo.map&"


def test_no_subdatasets_returns_false():
    m = {}

    assert process_wms_catalog(m, {"bands": [], "metadata": {}}) is False
    assert m == {}


def test_process_wms_catalog(wms_data):
    m = {}

    assert process_wms_catalog(m, wms_data) is True
    assert m["projection"] == "EPSG:4326"
    assert m["size"] == [1024, 512]
    # Half a pixel in from the outer edges, which removes the white border
    assert m["extent"] == [-179.8242, -89.8242, 179.8242, 89.8242]

    assert [lyr["name"] for lyr in m["layers"]] == ["bluemarble", "cities"]
    assert m["layers"][0] == {
        "__type__": "layer",
        "name": "bluemarble",
        "type": "raster",
        "status": "on",
        "connectiontype": "wms",
        "connection": f"{SERVER}?",
        "projection": "EPSG:4326",
        "metadata": {
            "__type__": "metadata",
            "wms_name": "bluemarble",
            "wms_title": "Blue Marble",
            "wms_srs": "EPSG:4326",
            "wms_server_version": "1.3.0",
            "wms_format": "image/png",
        },
    }

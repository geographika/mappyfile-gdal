import pytest

from mappyfile_gdal.vector import (
    layer_type,
    padded_bounds,
    process_vector,
)

WGS84 = {"projjson": {"id": {"authority": "EPSG", "code": 4326}}}


def make_layer(name, geom_type, extent=None, crs=WGS84):
    return {
        "name": name,
        "geometryFields": [
            {
                "type": geom_type,
                "extent": extent or [0, 0, 10, 10],
                "coordinateSystem": crs,
            }
        ],
    }


@pytest.fixture
def vector_data():
    """Cut-down gdal vector info JSON with one polygon layer."""
    return {
        "description": "data/mvt/point_polygon/1/1/1.pbf",
        "layers": [make_layer("polygon2", "MultiPolygon")],
    }


@pytest.mark.parametrize(
    "geom_type,expected",
    [
        ("MultiPolygon", "polygon"),
        ("LineString", "line"),
        ("Point", "point"),
        ("MultiPointZ", "point"),  # Z/M variants
        ("CompoundCurve", "line"),  # curve types
        ("GeometryCollection", None),
    ],
)
def test_layer_type(geom_type, expected):
    assert layer_type(geom_type) == expected


def test_bounds_are_padded():
    assert padded_bounds([[0, 0, 100, 100]]) == [-5.0, -5.0, 105.0, 105.0]


def test_single_point_bounds_get_a_unit_of_padding():
    # A zero-size extent would be rejected by MapServer
    assert padded_bounds([[5, 5, 5, 5]]) == [4.0, 4.0, 6.0, 6.0]


def test_process_vector(vector_data):
    m = {}
    process_vector(m, vector_data)

    assert m["projection"] == "EPSG:4326"
    assert m["size"] == [1600, 1600]
    assert m["resolution"] == 144

    assert m["layers"] == [
        {
            "__type__": "layer",
            "name": "polygon2",
            "type": "polygon",
            "status": "on",
            "connectiontype": "ogr",
            "connection": "data/mvt/point_polygon/1/1/1.pbf",
            "data": "polygon2",
            "classes": [
                {
                    "__type__": "class",
                    "styles": [
                        {"__type__": "style", "color": "#9ecae1", "opacity": 30},
                        {"__type__": "style", "outlinecolor": "#9ecae1", "width": 1},
                    ],
                }
            ],
            "projection": "EPSG:4326",
        }
    ]


def test_layers_are_drawn_polygons_first_points_last(vector_data):
    vector_data["layers"] = [
        make_layer("cities", "Point"),
        make_layer("land", "Polygon"),
        make_layer("rivers", "LineString"),
    ]
    m = {}
    process_vector(m, vector_data)

    assert [lyr["name"] for lyr in m["layers"]] == ["land", "rivers", "cities"]
    assert m["symbols"]  # a circle symbol is added for the point layer


def test_each_layer_gets_its_own_color(vector_data):
    vector_data["layers"] = [make_layer(f"l{i}", "Polygon") for i in range(3)]
    m = {}
    process_vector(m, vector_data)

    colors = [lyr["classes"][0]["styles"][0]["color"] for lyr in m["layers"]]
    assert len(set(colors)) == 3


def test_layers_without_geometry_are_skipped(vector_data):
    vector_data["layers"] = [{"name": "attributes_only", "geometryFields": []}]
    m = {}
    process_vector(m, vector_data)

    assert "layers" not in m  # nothing drawable, so the map is left empty

import json

from mappyfile_gdal.cli import main

RASTER_JSON = {
    "driverShortName": "GTiff",
    "description": "byte.tif",
    "files": ["byte.tif"],
    "size": [20, 20],
    "cornerCoordinates": {"lowerLeft": [0, 0], "upperRight": [200, 200]},
    "bands": [{"band": 1, "minimum": 0.0, "maximum": 255.0}],
    "stac": {"proj:epsg": 4326},
}


def test_mapfile_is_written(tmp_path):
    src = tmp_path / "byte.json"
    src.write_text(json.dumps(RASTER_JSON), encoding="utf-8")
    out = tmp_path / "byte.map"

    assert main([str(src), str(out)]) == 0
    assert "LAYER" in out.read_text(encoding="utf-8")


def test_mapfile_is_printed_without_an_output_path(tmp_path, capsys):
    src = tmp_path / "byte.json"
    src.write_text(json.dumps(RASTER_JSON), encoding="utf-8")

    assert main([str(src)]) == 0
    assert "MAP" in capsys.readouterr().out


def test_missing_input_file_is_an_error(tmp_path):
    assert main([str(tmp_path / "nope.json"), str(tmp_path / "out.map")]) == 1


def test_a_bad_json_file_is_reported_but_does_not_raise(tmp_path):
    src = tmp_path / "broken.json"
    src.write_text("not json", encoding="utf-8")

    assert main([str(src), str(tmp_path / "out.map")]) == 1

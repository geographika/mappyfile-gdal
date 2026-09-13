"""
Compare the Mapfile generated from each sample JSON file against an expected copy.

Expected files are written on the first run, so a new sample only needs its JSON
adding to tests/json/. Review and commit the generated Mapfile.

To update the expected files after an intentional change:

    pytest tests/test_expected.py --update-expected
"""

import json
from pathlib import Path

import pytest

from mappyfile_gdal.main import main as build_mapfile

JSON_DIR = Path(__file__).parent / "json"
EXPECTED_DIR = Path(__file__).parent / "mapfiles"


def sample_files():
    """
    Every sample JSON file, as (kind, path) pairs for the raster and vector folders
    """
    for kind in ("raster", "vector"):
        for path in sorted((JSON_DIR / kind).glob("*.json")):
            yield kind, path


def sample_id(sample):
    kind, path = sample
    return f"{kind}/{path.stem}"


@pytest.mark.parametrize("sample", sample_files(), ids=sample_id)
def test_mapfile_matches_expected(sample, request):
    kind, json_file = sample
    expected = EXPECTED_DIR / kind / f"{json_file.stem}.map"

    data = json.loads(json_file.read_text(encoding="utf-8"))
    generated = build_mapfile(data)

    if not expected.exists() or request.config.getoption("--update-expected"):
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.write_text(generated, encoding="utf-8")
        pytest.skip(f"wrote expected file {expected.relative_to(EXPECTED_DIR.parent)}")

    assert generated == expected.read_text(encoding="utf-8")

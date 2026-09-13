from pathlib import Path
from typing import Any

import mappyfile

from .raster import process_raster
from .vector import process_vector
from .wms import process_wms_catalog

from .drivers import RASTER_DRIVERS, VECTOR_DRIVERS

# use high quality PNG24 output format by default

PNG24 = {
    "__type__": "outputformat",
    "name": "png24",
    "driver": "AGG/PNG",
    "mimetype": "image/png",
    "imagemode": "rgb",
    "extension": "png",
}


def dataset_type(data: dict[str, Any]) -> str:
    """
    Check if the gdal info JSON is for a raster
    or vector dataset, first based on the driver, and for drivers that support both
    check for the JSON keys for 'layers' or 'bands'

    Raises an error if the driver is unknown and neither key is present,
    or returns 'raster' or 'vector'.
    """

    driver = data.get("driverShortName")
    is_raster = driver in RASTER_DRIVERS
    is_vector = driver in VECTOR_DRIVERS

    # driver only supports one type
    if is_raster and not is_vector:
        return "raster"
    if is_vector and not is_raster:
        return "vector"

    # driver supports both (e.g. GPKG) or isn't in either list, so check for keys in the JSON
    if "layers" in data:
        return "vector"  # gdal vector info output
    if "bands" in data:
        return "raster"  # gdal raster info output
    raise ValueError(
        f"Can't tell if {driver} JSON is raster or vector (no 'layers' or 'bands')"
    )


def build_map(data: dict[str, Any], shapepath: str | None = None) -> dict[str, Any]:
    """
    Build a mappyfile map from gdal info JSON
    """

    m = {
        "__type__": "map",
        "name": "GDAL",
        "size": [800, 800],
        "outputformats": [PNG24],
        "imagetype": "png24",
    }

    if shapepath:
        m["shapepath"] = shapepath

    driver = data.get("driverShortName")

    if driver == "WMS" and process_wms_catalog(m, data):
        pass  # WMS capabilities catalog so use MapServer CONNECTIONTYPE WMS layers
    elif dataset_type(data) == "raster":
        process_raster(m, data)
    else:
        process_vector(m, data)

    return m


def main(
    data: dict[str, Any],
    mapfile: str | Path | None = None,
    shapepath: str | None = None,
) -> Path | str:
    """
    Create a Mapfile from gdal info JSON.

    If mapfile is given, saves the Mapfile and returns the saved path.
    If mapfile is None, returns the Mapfile as a string.
    """

    m = build_map(data, shapepath)

    if mapfile:
        mapfile = Path(mapfile)
        mappyfile.save(m, str(mapfile))
        return mapfile

    return mappyfile.dumps(m)

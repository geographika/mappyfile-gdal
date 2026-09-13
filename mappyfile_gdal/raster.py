from pathlib import PurePosixPath
import math
from typing import Any
from .utils import get_projection, mapserver_extent
import logging

logger = logging.getLogger(__name__)

MIN_SIZE = 256
MAX_SIZE = 4096


def get_extent(data: dict[str, Any], size: list[int]) -> list[float]:
    ll = data["cornerCoordinates"]["lowerLeft"]
    ur = data["cornerCoordinates"]["upperRight"]
    return mapserver_extent(ll[0], ll[1], ur[0], ur[1], size)


def get_map_size(
    width: int, height: int, min_size: int = MIN_SIZE, max_size: int = MAX_SIZE
) -> list[int]:
    """
    Return the MAP SIZE for a raster of ``width`` x ``height`` cells, keeping the
    aspect ratio.
    The size will also be made to fit between min_size and max_size.
    """
    longest = max(width, height)
    factor: float

    if longest < min_size:
        factor = min(math.ceil(min_size / longest), max_size // longest)
    elif longest > max_size:
        factor = max_size / longest
    else:
        factor = 1

    return [max(1, round(width * factor)), max(1, round(height * factor))]


def get_scale(data: dict[str, Any]) -> tuple[float, float] | None:
    """
    Return (min, max) for PROCESSING SCALE, or None to let MapServer auto-scale.
    """
    # Only single-band rasters without a palette get a grayscale stretch
    bands = data.get("bands", [])
    if len(bands) != 1 or "colorTable" in bands[0]:
        return None

    bmin, bmax = bands[0].get("minimum"), bands[0].get("maximum")
    if bmin is None or bmax is None or bmin >= bmax:
        return None

    return bmin, bmax


def process_raster(m: dict[str, Any], data: dict[str, Any]) -> None:

    path = PurePosixPath(data["description"].replace("\\", "/"))

    lyr = {
        "__type__": "layer",
        "name": path.stem,
        "type": "raster",
        "status": "on",
        "data": data["files"][0].replace("\\", "/"),
    }

    processing = []

    # without a SCALE, MapServer uses SCALE=AUTO, computed per request
    scale = get_scale(data)
    if scale:
        # round to 6 significant digits
        processing.append(f"SCALE={scale[0]:.6g},{scale[1]:.6g}")

    # MapServer reads the nodata value from the raster file
    # so has no effect, unless CLASSes are used, but no harm adding anyway
    nodata = data.get("bands", [{}])[0].get("noDataValue")
    if nodata is not None:
        processing.append(f"NODATA={nodata}")

    if processing:
        lyr["processing"] = processing

    projection = get_projection(data.get("stac", {}).get("proj:projjson"))
    if projection:
        m["projection"] = projection
        lyr["projection"] = projection
    else:
        # MapServer draws the raster in its native CRS, matching the EXTENT
        logger.debug("%s: no EPSG code, PROJECTION not set", lyr["name"])

    m["size"] = get_map_size(*data["size"])
    m["extent"] = get_extent(data, m["size"])
    m["layers"] = [lyr]

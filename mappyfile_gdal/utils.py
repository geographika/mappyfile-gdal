import math
from typing import Any, Sequence


def get_projection(projjson: dict[str, Any] | None) -> str | None:
    """
    Return 'AUTHORITY:CODE' from a PROJJSON object, or None if it has no identifier.
    """
    projjson = projjson or {}
    ident = projjson.get("id") or next(iter(projjson.get("ids", [])), None)
    if ident and "authority" in ident and "code" in ident:
        return f"{ident['authority']}:{ident['code']}"
    return None


def mapserver_extent(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    size: Sequence[int],
    pixel_fraction: float = 0.001,
) -> list[float]:
    """
    Convert outer-edge bounds to a MapServer EXTENT (centers of the corner pixels)
    MapServer treats EXTENT as the centers of the corner pixels, while gdal info's cornerCoordinates are the outer edges
    rounded
    """
    px = (maxx - minx) / size[0]
    py = (maxy - miny) / size[1]

    precision = min(abs(px), abs(py)) * pixel_fraction
    decimals = max(0, math.ceil(-math.log10(precision)))

    extent = [minx + px / 2, miny + py / 2, maxx - px / 2, maxy - py / 2]
    return [round(v, decimals) for v in extent]

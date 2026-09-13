from typing import Any, NamedTuple, Sequence
from .utils import get_projection, mapserver_extent
import logging

logger = logging.getLogger(__name__)

MAP_LONGEST_SIDE = 800  # at normal resolution
RESOLUTION_SCALE = (
    2  # render at 2x pixel density; widths and symbol sizes scale to match
)

PALETTE = [
    "#9ecae1",  # pale sky blue
    "#f2d49b",  # sand
    "#a8d5ba",  # sage
    "#e8a598",  # muted coral
    "#c3b1e1",  # lavender
    "#f5f0e1",  # chalk white
    "#89c2c2",  # grey teal
    "#d4b483",  # khaki
    "#b5c7d3",  # steel
    "#e6c2d6",  # dusty pink
]
FILL_OPACITY = 30  # percent; fills are see-through, lines and outlines stay solid

# Draw order: polygons at the bottom, points on top
DRAW_ORDER = {"polygon": 0, "line": 1, "point": 2}

CIRCLE_SYMBOL = {
    "__type__": "symbol",
    "name": "circle",
    "type": "ellipse",
    "filled": True,
    "points": [[1, 1]],
}


# A MapServer layer with the CRS and extent needed to compute the map extent
class LayerInfo(NamedTuple):
    layer: dict[str, Any]
    projection: str | None
    extent: list[float] | None


def layer_type(geom_type: str) -> str | None:
    """
    Map an OGR geometry type name to a MapServer layer type, or None if unsupported.
    """
    t = geom_type.lower()  # also covers Z/M types, e.g. "MultiPolygonZ"
    if "polygon" in t or "surface" in t or "triangle" in t or t.startswith("tin"):
        return "polygon"
    if "line" in t or "curve" in t or "circularstring" in t:
        return "line"
    if "point" in t:
        return "point"
    return None  # for example GeometryCollection, Unknown


def make_style(**kwargs: Any) -> dict[str, Any]:
    return {"__type__": "style", **kwargs}


def make_class(ltype: str, color: str) -> dict[str, Any]:
    if ltype == "polygon":
        styles = [
            make_style(color=color, opacity=FILL_OPACITY),
            make_style(outlinecolor=color, width=1),
        ]
    elif ltype == "line":
        styles = [make_style(color=color, width=1)]
    else:
        # simple point style with a transparent fill and no outline
        styles = [
            make_style(symbol="circle", size=8, color=color, opacity=FILL_OPACITY)
        ]

    return {"__type__": "class", "styles": styles}


def padded_bounds(
    extents: Sequence[Sequence[float]], fraction: float = 0.05
) -> list[float]:
    """
    Union of layer extents with a margin, so features at the edges aren't clipped.
    """
    minx = min(e[0] for e in extents)
    miny = min(e[1] for e in extents)
    maxx = max(e[2] for e in extents)
    maxy = max(e[3] for e in extents)
    pad = (
        max(maxx - minx, maxy - miny) * fraction or 1.0
    )  # 1 map unit for a single point
    return [minx - pad, miny - pad, maxx + pad, maxy + pad]


def size_for_bounds(
    bounds: Sequence[float], longest: int = MAP_LONGEST_SIDE
) -> list[int]:
    w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
    if w >= h:
        return [longest, max(1, round(longest * h / w))]
    return [max(1, round(longest * w / h)), longest]


def process_vector(m: dict[str, Any], data: dict[str, Any]) -> None:
    layers: list[LayerInfo] = []

    for gdal_layer in data.get("layers", []):
        name = gdal_layer["name"]
        geom_fields = gdal_layer.get("geometryFields", [])

        if not geom_fields:
            logger.warning("%s: no geometry, skipped", name)
            continue
        if len(geom_fields) > 1:
            logger.warning(
                "%s: %d geometry fields, using the first", name, len(geom_fields)
            )

        geom_field = geom_fields[0]

        ltype = layer_type(geom_field["type"])
        if ltype is None:
            logger.warning(
                "%s: %s not yet supported, skipped", name, geom_field["type"]
            )
            continue

        color = PALETTE[
            len(layers) % len(PALETTE)
        ]  # next color for each drawable layer

        lyr = {
            "__type__": "layer",
            "name": name,
            "type": ltype,
            "status": "on",
            "connectiontype": "ogr",
            "connection": data["description"].replace("\\", "/"),
            "data": name,  # selects this layer within the dataset
            "classes": [make_class(ltype, color)],
        }

        projection = get_projection(
            (geom_field.get("coordinateSystem") or {}).get("projjson")
        )
        if projection:
            lyr["projection"] = projection

        layers.append(LayerInfo(lyr, projection, geom_field.get("extent")))

    if not layers:
        logger.warning("No drawable layers found")
        return

    layers.sort(key=lambda item: DRAW_ORDER[item.layer["type"]])

    # the Map uses the first CRS found,
    # any layers in other CRSs are reprojected by MapServer
    map_projection = next((i.projection for i in layers if i.projection), None)
    if map_projection:
        m["projection"] = map_projection

    # Only extents already in the map's CRS can be combined directly
    extents = [i.extent for i in layers if i.extent and i.projection == map_projection]
    if extents:
        minx, miny, maxx, maxy = padded_bounds(extents)
        m["size"] = size_for_bounds(
            [minx, miny, maxx, maxy], MAP_LONGEST_SIDE * RESOLUTION_SCALE
        )
        m["extent"] = mapserver_extent(minx, miny, maxx, maxy, m["size"])
        # Pixel sizes in styles (WIDTH, SIZE) are scaled by RESOLUTION / DEFRESOLUTION
        m["resolution"] = 72 * RESOLUTION_SCALE
        m["defresolution"] = 72

    if any(i.layer["type"] == "point" for i in layers):
        m["symbols"] = [CIRCLE_SYMBOL]

    m["layers"] = [i.layer for i in layers]

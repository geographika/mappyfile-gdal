import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from .utils import mapserver_extent

# GetMap parameters MapServer adds itself; anything else (e.g. map=) stays in CONNECTION
WMS_PARAMS = {
    "SERVICE",
    "VERSION",
    "REQUEST",
    "LAYERS",
    "STYLES",
    "CRS",
    "SRS",
    "BBOX",
    "WIDTH",
    "HEIGHT",
    "FORMAT",
    "TRANSPARENT",
}


def parse_wms_subdatasets(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return WMS layer settings from a gdal info catalog, or [] if there are none
    """
    subdatasets = data.get("metadata", {}).get("SUBDATASETS", {})
    numbers = sorted(
        int(m.group(1))
        for key in subdatasets
        if (m := re.fullmatch(r"SUBDATASET_(\d+)_NAME", key))
    )
    layers = []

    for n in numbers:
        name = subdatasets[f"SUBDATASET_{n}_NAME"]
        if not name.startswith("WMS:"):
            continue

        url = urlsplit(name.removeprefix("WMS:"))
        params = {k.upper(): v[0] for k, v in parse_qs(url.query).items()}
        extra = {k: v for k, v in params.items() if k not in WMS_PARAMS}

        base = urlunsplit((url.scheme, url.netloc, url.path, "", ""))
        version = params.get("VERSION", "1.3.0")
        crs = params.get("CRS") or params.get("SRS", "EPSG:4326")
        bbox = [float(v) for v in params["BBOX"].split(",")]

        # WMS 1.3.0 gives EPSG:4326 bboxes as lat/lon; MapServer extents are lon/lat
        if version == "1.3.0" and crs.upper() == "EPSG:4326":
            bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]

        layers.append(
            {
                "name": params["LAYERS"],
                "title": subdatasets.get(f"SUBDATASET_{n}_DESC", params["LAYERS"]),
                "connection": f"{base}?{urlencode(extra)}&" if extra else f"{base}?",
                "version": version,
                "crs": crs,
                "extent": bbox,
            }
        )

    return layers


def process_wms_catalog(
    m: dict[str, Any], data: dict[str, Any], width: int = 1024
) -> bool:
    wms_layers = parse_wms_subdatasets(data)
    if not wms_layers:
        return False

    m["projection"] = wms_layers[0]["crs"]

    extents = [layer["extent"] for layer in wms_layers]
    minx = min(e[0] for e in extents)
    miny = min(e[1] for e in extents)
    maxx = max(e[2] for e in extents)
    maxy = max(e[3] for e in extents)

    m["size"] = [width, max(1, round(width * (maxy - miny) / (maxx - minx)))]
    m["extent"] = mapserver_extent(minx, miny, maxx, maxy, m["size"])

    layers = []
    for wms in wms_layers:
        lyr = {
            "__type__": "layer",
            "name": wms["name"],
            "type": "raster",
            "status": "on",
            "connectiontype": "wms",
            "connection": wms["connection"],
            "projection": wms["crs"],
            "metadata": {
                "__type__": "metadata",
                "wms_name": wms["name"],
                "wms_title": wms["title"],
                "wms_srs": wms["crs"],
                "wms_server_version": wms["version"],
                "wms_format": "image/png",
            },
        }
        layers.append(lyr)

    m["layers"] = layers
    return True

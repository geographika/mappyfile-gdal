"""
Build renderable Mapfiles from the sample JSON, with a SHAPEPATH so the
relative DATA paths resolve. The output is gitignored; tests/mapfiles holds
the machine-independent expected copies.

    python ./scripts/build_render_mapfiles.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Where the relative paths in each folder's JSON files are rooted
SHAPEPATHS = {
    "raster": "C:/docs/gdal/autotest/gdrivers/data",
    "vector": "C:/docs/gdal/autotest/ogr",
}


def main() -> int:
    for kind, shapepath in SHAPEPATHS.items():
        result = subprocess.run(
            [
                "mappyfile-gdal",
                str(ROOT / "tests/json" / kind),
                str(ROOT / "scripts/mapfiles" / kind),
                "--shapepath",
                shapepath,
            ]
        )
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())

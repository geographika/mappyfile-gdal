"""
Print a map2img command for each Mapfile in a folder tree.

    python ./scripts/create_map2img_commands.py scripts/mapfiles

The output path is relative to the Mapfile's own folder, which is how map2img
resolves -o, so ../../scripts/output from scripts/mapfiles/vector means scripts/output/vector.
"""

import argparse
import sys
from pathlib import Path

DEBUG_LEVEL = 5


def build_command(mapfile: Path, map_dir: Path, out_dir: str, debug: int) -> str:
    """
    Return the map2img command for one Mapfile.
    """
    # Mirror the raster/vector subfolders in the output
    subfolder = mapfile.parent.relative_to(map_dir)
    png = Path(out_dir) / subfolder / f"{mapfile.stem}.png"

    cmd = f"map2img -m {mapfile.as_posix()} -o {png.as_posix()}"
    if debug:
        cmd += f" -all_debug {debug}"
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "map_dir", type=Path, help="Folder of Mapfiles, searched recursively"
    )
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="../../output",
        help="PNG folder, relative to each Mapfile's folder (default: ../../output)",
    )
    parser.add_argument(
        "--debug",
        type=int,
        default=DEBUG_LEVEL,
        help=f"-all_debug level, 0 to omit (default: {DEBUG_LEVEL})",
    )
    args = parser.parse_args(argv)

    mapfiles = sorted(args.map_dir.rglob("*.map"))

    if not mapfiles:
        print(f"No Mapfiles found in {args.map_dir}", file=sys.stderr)
        return 1

    for mapfile in mapfiles:
        print(build_command(mapfile, args.map_dir, args.out_dir, args.debug))

    return 0


if __name__ == "__main__":
    sys.exit(main())

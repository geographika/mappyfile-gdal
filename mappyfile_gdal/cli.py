import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import logging

from mappyfile_gdal import __version__
from mappyfile_gdal.main import main as build_mapfile

logger = logging.getLogger(__name__)


def parse_file(fn: str | Path) -> dict:
    """
    Open a gdal info JSON file and return its parsed contents
    """
    file_path = Path(fn)

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_files(input_path: Path) -> list[Path]:
    """
    Return the JSON files to process: a single file, or every *.json in a folder.
    """
    if input_path.is_dir():
        return sorted(input_path.glob("*.json"))
    return [input_path]


def write_mapfile(
    data: dict, output_path: Optional[Path], shapepath: Optional[str]
) -> None:
    """
    Save the Mapfile, or print to stdout when there is no output path.
    """
    if output_path is None:
        print(build_mapfile(data, shapepath=shapepath))
        return

    saved = build_mapfile(data, output_path, shapepath=shapepath)
    print(f"OK: {saved}")


def main(argv: Optional[list[str]] = None) -> int:
    """
    CLI entry point for mappyfile-gdal.
    Returns an exit code: 0 = success, non-zero = error.
    """

    parser = argparse.ArgumentParser(
        prog="mappyfile-gdal",
        description="Create MapServer Mapfiles from gdal info JSON",
        epilog="Reads JSON from stdin when input_path is omitted or '-', e.g. "
        "gdal raster info byte.tif | mappyfile-gdal - byte.map",
    )

    parser.add_argument(
        "input_path",
        nargs="?",
        help="Path to a gdal info JSON file, or a folder of JSON files "
        "(default: read JSON from stdin)",
    )

    parser.add_argument(
        "output_path",
        nargs="?",
        help="Path to save the Mapfile, or a folder when input_path is a folder "
        "(default: print the Mapfile to stdout)",
    )

    parser.add_argument(
        "--shapepath",
        default=None,
        help="SHAPEPATH for the Mapfile, so layer DATA and CONNECTION can stay relative",
    )

    verbosity = parser.add_mutually_exclusive_group()

    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show debug messages",
    )

    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only show errors",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"mappyfile-gdal {__version__}",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    use_stdin = args.input_path in (None, "-")

    # Without piped input there is nothing to read, so show the help instead of hanging
    if use_stdin and sys.stdin.isatty():
        parser.print_help()
        return 1

    output_path = Path(args.output_path) if args.output_path else None

    if use_stdin:
        raw = sys.stdin.read()

        if not raw.strip():
            logger.error(
                "No input received on stdin. Check the gdal info command succeeded "
                "and used --of json."
            )
            return 1

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(
                "stdin is not valid JSON: %s. Check the output of the gdal info command.",
                exc,
            )
            return 1

        try:
            write_mapfile(data, output_path, args.shapepath)
        except Exception as exc:
            logger.error("%s: %s", type(exc).__name__, exc)
            return 1

        return 0

    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error("File '%s' does not exist.", args.input_path)
        return 1

    files = json_files(input_path)
    if not files:
        logger.error("No JSON files found in '%s'.", args.input_path)
        return 1

    if input_path.is_dir() and not output_path:
        parser.error("output_path is required when input_path is a folder")

    if output_path and len(files) > 1:
        output_path.mkdir(parents=True, exist_ok=True)

    failed = 0

    for json_file in files:
        try:
            data = parse_file(json_file)

            # A folder of inputs names each Mapfile after its JSON file
            file_output = (
                output_path / json_file.with_suffix(".map").name
                if output_path and len(files) > 1
                else output_path
            )

            write_mapfile(data, file_output, args.shapepath)
        except Exception as exc:
            failed += 1
            logger.error("%s -> %s: %s", json_file.name, type(exc).__name__, exc)

    if failed:
        logger.error("%d of %d file(s) failed.", failed, len(files))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

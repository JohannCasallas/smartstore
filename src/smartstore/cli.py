from __future__ import annotations

import argparse
import sys
from pathlib import Path

from smartstore.common.config import get_paths
from smartstore.ingestion.profiler import profile_dataset_directory, write_profile_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartstore",
        description="SmartStore — analítica comercial y pronóstico de demanda.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser(
        "profile",
        help="Perfila CSVs en data/raw y genera informe JSON + Markdown.",
    )
    profile.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Carpeta con CSV (por defecto: data/raw del proyecto).",
    )
    profile.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Carpeta de salida (por defecto: docs/reports).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    paths = get_paths()

    if args.command == "profile":
        data_dir = args.data_dir or paths.data_raw
        output_dir = args.output_dir or paths.docs_reports
        if not data_dir.is_dir():
            print(f"Error: no existe el directorio de datos: {data_dir}", file=sys.stderr)
            return 1

        payload = profile_dataset_directory(data_dir)
        json_path, md_path = write_profile_report(payload, output_dir)
        print(f"Perfilado completado ({payload['summary']['csv_files_found']} archivos).")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        missing = payload["summary"].get("missing_expected_files") or []
        if missing:
            print(
                f"  Aviso: faltan {len(missing)} archivo(s) esperados del dataset Olist.",
                file=sys.stderr,
            )
            return 2
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

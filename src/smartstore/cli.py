from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from smartstore.analytics.metrics import (
    EnrichedTableError,
    compute_commercial_metrics,
    load_enriched_table,
)
from smartstore.analytics.report import write_analytics_report
from smartstore.common.config import get_paths
from smartstore.forecasting.baseline import select_baseline
from smartstore.forecasting.report import build_forecast_frame, write_forecast_report
from smartstore.forecasting.series import ForecastError, weekly_item_demand
from smartstore.ingestion.profiler import profile_dataset_directory, write_profile_report
from smartstore.ingestion.transform import (
    ENRICHED_FILENAME,
    MissingCoreTablesError,
    build_processed_table,
)
from smartstore.ingestion.validate import validate_and_write_report


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
    _add_io_args(profile)

    validate = sub.add_parser(
        "validate",
        help="Valida integridad Olist, fechas y definición de venta.",
    )
    _add_io_args(validate)

    build = sub.add_parser(
        "build",
        help="Construye data/processed/order_items_enriched.csv (granularidad ítem).",
    )
    _add_io_args(build, output_help="Carpeta de salida (por defecto: data/processed).")

    analyze = sub.add_parser(
        "analyze",
        help="KPIs y demanda semanal sobre ventas válidas (is_valid_sale).",
    )
    analyze.add_argument(
        "--input",
        type=Path,
        default=None,
        help=f"CSV analítico (por defecto: data/processed/{ENRICHED_FILENAME}).",
    )
    analyze.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Carpeta de salida (por defecto: docs/reports).",
    )
    analyze.add_argument(
        "--top-n",
        type=int,
        default=15,
        help="Cuántos vendedores incluir, ordenados por ingreso.",
    )

    forecast = sub.add_parser(
        "forecast",
        help="Pronostica ítems vendidos por semana y compara tres modelos simples.",
    )
    forecast.add_argument(
        "--input",
        type=Path,
        default=None,
        help=f"CSV analítico (por defecto: data/processed/{ENRICHED_FILENAME}).",
    )
    forecast.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Carpeta de informes (por defecto: docs/reports).",
    )
    forecast.add_argument(
        "--series-dir",
        type=Path,
        default=None,
        help="Carpeta de las series CSV (por defecto: data/processed).",
    )
    forecast.add_argument(
        "--horizon",
        type=int,
        default=8,
        help="Semanas a pronosticar.",
    )
    return parser


def _add_io_args(
    parser: argparse.ArgumentParser,
    *,
    output_help: str = "Carpeta de salida (por defecto: docs/reports).",
) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Carpeta con CSV (por defecto: data/raw del proyecto).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=output_help,
    )


def _require_data_dir(data_dir: Path) -> int | None:
    if not data_dir.is_dir():
        print(f"Error: no existe el directorio de datos: {data_dir}", file=sys.stderr)
        return 1
    return None


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    paths = get_paths()

    if args.command == "profile":
        data_dir = args.data_dir or paths.data_raw
        err = _require_data_dir(data_dir)
        if err is not None:
            return err
        output_dir = args.output_dir or paths.docs_reports
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

    if args.command == "validate":
        data_dir = args.data_dir or paths.data_raw
        err = _require_data_dir(data_dir)
        if err is not None:
            return err
        output_dir = args.output_dir or paths.docs_reports
        payload, json_path, md_path = validate_and_write_report(data_dir, output_dir)
        summary = payload["summary"]
        status = "PASS" if summary["passed"] else "FAIL"
        failed = summary["checks_failed"]
        warned = summary["checks_warned"]
        print(f"Validación {status} (fallos={failed}, avisos={warned}).")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        if not summary["passed"]:
            return 2
        return 0

    if args.command == "build":
        data_dir = args.data_dir or paths.data_raw
        err = _require_data_dir(data_dir)
        if err is not None:
            return err
        output_dir = args.output_dir or paths.data_processed
        try:
            frame, path = build_processed_table(data_dir, output_dir)
        except MissingCoreTablesError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        n_sales = int(frame["is_valid_sale"].sum())
        print(f"Tabla analítica: {len(frame)} líneas ({n_sales} ventas válidas).")
        print(f"  CSV: {path}")
        return 0

    if args.command == "analyze":
        source = args.input or (paths.data_processed / ENRICHED_FILENAME)
        output_dir = args.output_dir or paths.docs_reports
        try:
            frame = load_enriched_table(source)
        except EnrichedTableError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        metrics = compute_commercial_metrics(frame, top_n=args.top_n)
        payload = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "source": str(source),
            **metrics,
        }
        json_path, md_path = write_analytics_report(payload, output_dir)
        summary = payload["summary"]
        print(
            "Análisis comercial: "
            f"{summary['orders_valid']} pedidos, "
            f"ingreso={summary['revenue']:.2f}."
        )
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        return 0

    if args.command == "forecast":
        source = args.input or (paths.data_processed / ENRICHED_FILENAME)
        output_dir = args.output_dir or paths.docs_reports
        series_dir = args.series_dir or paths.data_processed
        try:
            frame = load_enriched_table(source)
            history = weekly_item_demand(frame)
        except (EnrichedTableError, ForecastError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        if args.horizon < 1:
            print("Error: --horizon debe ser al menos 1.", file=sys.stderr)
            return 2
        result = select_baseline(history["items"].astype(float).tolist(), horizon=args.horizon)
        forecast = build_forecast_frame(history["week_start"].iloc[-1], result["future_items"])
        payload = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "source": str(source),
            "horizon": args.horizon,
            "demand": "items_per_iso_week",
            "chosen_model": result["chosen_model"],
            "chosen_label": result["chosen_label"],
            "holdout_weeks": result["holdout_weeks"],
            "evaluations": result["evaluations"],
            "forecast": [
                {
                    "purchase_year": int(row.purchase_year),
                    "purchase_week": int(row.purchase_week),
                    "items": float(row.items),
                }
                for row in forecast.itertuples(index=False)
            ],
        }
        series_dir.mkdir(parents=True, exist_ok=True)
        history_path = series_dir / "weekly_item_demand.csv"
        forecast_path = series_dir / "item_demand_forecast.csv"
        history.to_csv(history_path, index=False)
        forecast.to_csv(forecast_path, index=False)
        json_path, md_path, chart_path = write_forecast_report(
            payload, output_dir, history, forecast
        )
        print(
            "Pronóstico: "
            f"{result['chosen_label']} "
            f"({args.horizon} semanas)."
        )
        print(f"  Histórico: {history_path}")
        print(f"  Pronóstico: {forecast_path}")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        print(f"  Gráfico: {chart_path}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

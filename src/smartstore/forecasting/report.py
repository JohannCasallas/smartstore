"""Informe y gráfico del pronóstico de demanda."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def build_forecast_frame(
    last_week_start: pd.Timestamp,
    future_items: list[float],
) -> pd.DataFrame:
    from smartstore.forecasting.baseline import future_weeks

    weeks = future_weeks(last_week_start, len(future_items))
    iso = weeks.isocalendar()
    return pd.DataFrame(
        {
            "week_start": weeks,
            "purchase_year": iso.year.astype(int).to_numpy(),
            "purchase_week": iso.week.astype(int).to_numpy(),
            "items": future_items,
        }
    )


def build_forecast_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Pronóstico de demanda",
        "",
        f"- **Generado:** {payload['generated_at']}",
        f"- **Fuente:** `{payload['source']}`",
        "- **Qué se pronostica:** ítems vendidos por semana (filas con `is_valid_sale`).",
        f"- **Horizonte:** {payload['horizon']} semanas.",
        f"- **Modelo elegido:** {payload['chosen_label']} (`{payload['chosen_model']}`).",
        f"- **Semanas usadas para medir el error:** {payload['holdout_weeks']}.",
        "",
        "El error es el MAE: el promedio de |real − pronóstico| en esas semanas. "
        "Cada predicción de la prueba usa solo las semanas anteriores, no el futuro.",
        "",
        "## Comparación",
        "",
    ]
    evaluations = payload.get("evaluations") or []
    if not evaluations:
        lines.append("La serie es demasiado corta para comparar modelos.")
        lines.append("")
    else:
        lines.extend(
            [
                "| Modelo | MAE |",
                "| --- | --- |",
            ]
        )
        for row in evaluations:
            mark = " ← elegido" if row["model"] == payload["chosen_model"] else ""
            lines.append(f"| {row['label']}{mark} | {row['mae']} |")
        lines.append("")

    lines.extend(["## Próximas semanas", ""])
    forecast = payload.get("forecast") or []
    if not forecast:
        lines.append("Sin horizonte.")
    else:
        lines.extend(
            [
                "| purchase_year | purchase_week | items |",
                "| --- | --- | --- |",
            ]
        )
        for row in forecast:
            lines.append(
                f"| {row['purchase_year']} | {row['purchase_week']} | {row['items']} |"
            )
    lines.extend(
        [
            "",
            "Estos números son una referencia para inventario. No son un compromiso de venta.",
            "",
        ]
    )
    return "\n".join(lines)


def write_forecast_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(history["week_start"], history["items"], label="histórico", color="#1f4e79")
    if not forecast.empty:
        ax.plot(
            forecast["week_start"],
            forecast["items"],
            label="pronóstico",
            color="#c45911",
            marker="o",
        )
    ax.set_title("Ítems vendidos por semana")
    ax.set_ylabel("ítems")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_forecast_report(
    payload: dict[str, Any],
    output_dir: Path,
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    *,
    prefix: str = "forecast",
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{stamp}.json"
    md_path = output_dir / f"{prefix}_{stamp}.md"
    chart_path = output_dir / f"{prefix}_{stamp}.png"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path.write_text(build_forecast_markdown(payload), encoding="utf-8")
    write_forecast_chart(history, forecast, chart_path)
    return json_path, md_path, chart_path

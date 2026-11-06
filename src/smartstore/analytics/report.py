"""Informe JSON + Markdown de la Fase 3."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_analytics_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines: list[str] = [
        "# Informe comercial",
        "",
        f"- **Generado:** {payload['generated_at']}",
        f"- **Fuente:** `{payload['source']}`",
        "- **Universo:** líneas con `is_valid_sale = true` (pedido `delivered`).",
        "- **Ingreso:** suma de `price`. El flete se informa aparte.",
        "",
        "## Resumen",
        "",
        f"- **Líneas totales / válidas / excluidas:** "
        f"{summary['lines_total']:,} / {summary['lines_valid']:,} / "
        f"{summary['lines_excluded']:,}",
        f"- **Pedidos válidos:** {summary['orders_valid']:,}",
        f"- **Ingreso (price):** {summary['revenue']:,.2f}",
        f"- **Flete:** {summary['freight']:,.2f}",
        f"- **Ticket promedio (ingreso / pedido):** {summary['average_order_value']:,.2f}",
        f"- **Ítems por pedido:** {summary['items_per_order']:.2f}",
        "",
        "## Demanda semanal",
        "",
    ]
    lines.extend(_table(
        payload.get("weekly_demand") or [],
        ["purchase_year", "purchase_week", "orders", "items", "revenue", "freight"],
    ))
    lines.extend(["", "## Categorías", ""])
    lines.extend(_table(
        payload.get("by_category") or [],
        ["category", "orders", "items", "revenue", "freight"],
    ))
    lines.extend(["", "## Estado del cliente", ""])
    lines.extend(_table(
        payload.get("by_state") or [],
        ["customer_state", "orders", "items", "revenue", "freight"],
    ))
    lines.extend(["", "## Vendedores (top)", ""])
    lines.extend(_table(
        payload.get("by_seller") or [],
        ["seller_id", "orders", "items", "revenue", "freight"],
    ))
    lines.extend(
        [
            "",
            "## Próximo paso (Fase 4)",
            "",
            "La serie `weekly_demand` es la entrada del pronóstico: una fila por "
            "semana ISO, solo ventas válidas, sin fechas de entrega ni reseñas.",
            "",
        ]
    )
    return "\n".join(lines)


def _table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    if not rows:
        return ["Sin filas.", ""]
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        cells = ["" if row.get(col) is None else str(row.get(col)) for col in columns]
        body.append("| " + " | ".join(cells) + " |")
    return [header, sep, *body, ""]


def write_analytics_report(
    payload: dict[str, Any],
    output_dir: Path,
    *,
    prefix: str = "analytics",
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{stamp}.json"
    md_path = output_dir / f"{prefix}_{stamp}.md"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path.write_text(build_analytics_markdown(payload), encoding="utf-8")
    return json_path, md_path

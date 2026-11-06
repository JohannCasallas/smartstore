from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KB", "MB", "GB"):
        value /= 1024
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
    return f"{value:.1f} GB"


def build_markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Informe de perfilado de datos",
        "",
        f"- **Generado:** {payload['generated_at']}",
        f"- **Directorio analizado:** `{payload['data_directory']}`",
        f"- **Archivos CSV encontrados:** {payload['summary']['csv_files_found']}",
        f"- **Tablas Olist esperadas presentes:** "
        f"{payload['summary']['expected_tables_present']}/"
        f"{payload['summary']['expected_tables_total']}",
        "",
    ]

    missing = payload["summary"].get("missing_expected_files") or []
    if missing:
        lines.extend(
            [
                "## Archivos esperados no encontrados",
                "",
                "Descarga el dataset desde Kaggle (Brazilian E-Commerce / Olist) "
                "y coloca los CSV en `data/raw/` sin modificarlos.",
                "",
            ]
        )
        for name in missing:
            lines.append(f"- `{name}`")
        lines.append("")

    lines.extend(["## Detalle por archivo", ""])
    for profile in payload["profiles"]:
        lines.append(f"### `{profile['file_name']}`")
        if profile.get("catalog_match"):
            spec = profile["catalog_match"]
            lines.append(f"- **Dominio:** {spec['description']}")
            if spec.get("notes"):
                lines.append(f"- **Nota:** {spec['notes']}")
        lines.append(f"- **Tamaño:** {_format_bytes(profile['file_size_bytes'])}")
        lines.append(f"- **Filas:** {profile['rows']:,} | **Columnas:** {profile['columns']}")
        lines.append(f"- **Filas duplicadas (exactas):** {profile['duplicate_rows']:,}")

        pk = profile.get("primary_key_check") or {}
        if pk:
            lines.append("- **Claves declaradas:**")
            for col, info in pk.items():
                status = "OK" if info["is_unique"] else "REVISAR"
                lines.append(
                    f"  - `{col}`: únicos={info['n_unique']:,}, "
                    f"nulos={info['n_null']:,} → **{status}**"
                )

        missing_cols = profile.get("missing_values") or {}
        cols_with_nulls = {k: v for k, v in missing_cols.items() if v > 0}
        if cols_with_nulls:
            lines.append("- **Valores faltantes (columnas con nulos):**")
            for col, count in sorted(cols_with_nulls.items(), key=lambda x: -x[1]):
                pct = profile["missing_pct"].get(col, 0)
                lines.append(f"  - `{col}`: {count:,} ({pct:.2f}%)")
        else:
            lines.append("- **Valores faltantes:** ninguno detectado.")

        lines.append("")
        lines.append("<details><summary>Tipos de datos</summary>")
        lines.append("")
        for col, dtype in profile["data_types"].items():
            lines.append(f"- `{col}`: {dtype}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.extend(
        [
            "## Próximos pasos (Fase 2)",
            "",
            "1. Documentar definición de venta y estados de pedido válidos.",
            "2. Validar integridad referencial entre tablas (claves foráneas).",
            "3. Construir tabla analítica con granularidad acordada.",
            "",
        ]
    )
    return "\n".join(lines)


def write_profile_report(
    payload: dict[str, Any],
    output_dir: Path,
    *,
    prefix: str = "data_profile",
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{stamp}.json"
    md_path = output_dir / f"{prefix}_{stamp}.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(build_markdown_report(payload), encoding="utf-8")
    return json_path, md_path


def build_quality_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    sale = payload.get("sale_definition") or {}
    lines: list[str] = [
        "# Informe de calidad de datos",
        "",
        f"- **Generado:** {payload['generated_at']}",
        f"- **Directorio analizado:** `{payload['data_directory']}`",
        f"- **Resultado:** {'PASS' if summary['passed'] else 'FAIL'}",
        f"- **Chequeos fallidos:** {summary['checks_failed']} | "
        f"**avisos:** {summary['checks_warned']}",
        "",
        "## Definición de venta (ADR 0002)",
        "",
        f"- **Estados válidos:** {', '.join(f'`{s}`' for s in sale.get('valid_statuses', []))}",
        f"- **Fecha de demanda:** `{sale.get('demand_timestamp', '')}`",
        f"- **Montos de línea:** "
        f"{', '.join(f'`{c}`' for c in sale.get('line_amount_columns', []))}",
        f"- **Documento:** `{sale.get('adr', '')}`",
        "",
    ]

    missing = summary.get("missing_expected_files") or []
    if missing:
        lines.extend(["## Archivos esperados no encontrados", ""])
        for name in missing:
            lines.append(f"- `{name}`")
        lines.append("")

    status_counts = payload.get("order_status_counts") or {}
    if status_counts:
        lines.extend(["## Distribución de `order_status`", ""])
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            marker = "venta" if status in set(sale.get("valid_statuses") or []) else "excluido"
            lines.append(f"- `{status}`: {count:,} ({marker})")
        lines.append("")

    lines.extend(["## Chequeos", ""])
    for check in payload.get("checks") or []:
        if check["passed"]:
            mark = "OK"
        elif check["severity"] == "warning":
            mark = "AVISO"
        else:
            mark = "ERROR"
        lines.append(f"- **{mark}** `{check['id']}` — {check['message']}")
    lines.append("")
    lines.extend(
        [
            "## Próximos pasos",
            "",
            "1. `smartstore build` si aún no existe `data/processed/order_items_enriched.csv`.",
            "2. `smartstore analyze` — KPIs y demanda semanal sobre ventas válidas.",
            "3. Fase 4: pronóstico a partir de la serie semanal del informe comercial.",
            "",
        ]
    )
    return "\n".join(lines)


def write_quality_report(
    payload: dict[str, Any],
    output_dir: Path,
    *,
    prefix: str = "data_quality",
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"{prefix}_{stamp}.json"
    md_path = output_dir / f"{prefix}_{stamp}.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(build_quality_markdown(payload), encoding="utf-8")
    return json_path, md_path

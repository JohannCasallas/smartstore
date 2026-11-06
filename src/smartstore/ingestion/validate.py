from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from smartstore.common.business_rules import (
    PK_WARNING_ONLY_FILES,
    SALE_DEFINITION,
    VALID_SALE_STATUSES,
)
from smartstore.common.olist_catalog import expected_olist_tables
from smartstore.ingestion.loaders import load_olist_tables
from smartstore.ingestion.report import write_quality_report


def _check(
    check_id: str,
    passed: bool,
    message: str,
    *,
    severity: str = "error",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "passed": passed,
        "severity": severity,
        "message": message,
        "details": details or {},
    }


def _parent_ref(ref: str) -> tuple[str, str]:
    table, column = ref.split(".", 1)
    return f"{table}.csv", column


def _primary_key_check(df: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, Any]:
    missing_cols = [c for c in columns if c not in df.columns]
    if missing_cols:
        return {
            "is_unique": False,
            "n_duplicate_keys": None,
            "missing_columns": missing_cols,
        }
    n_null_rows = int(df[list(columns)].isna().any(axis=1).sum())
    duplicated = df.duplicated(subset=list(columns), keep=False)
    n_duplicate_keys = int(df.loc[duplicated, list(columns)].drop_duplicates().shape[0])
    is_unique = n_null_rows == 0 and n_duplicate_keys == 0
    return {
        "is_unique": is_unique,
        "n_duplicate_keys": n_duplicate_keys,
        "n_null_key_rows": n_null_rows,
        "missing_columns": [],
    }


def _foreign_key_check(
    child: pd.DataFrame,
    child_col: str,
    parent: pd.DataFrame,
    parent_col: str,
) -> dict[str, Any]:
    if child_col not in child.columns:
        return {"column_present": False, "n_orphan": None, "n_checked": 0}
    if parent_col not in parent.columns:
        return {
            "column_present": True,
            "parent_column_present": False,
            "n_orphan": None,
            "n_checked": int(child[child_col].notna().sum()),
        }
    child_ids = child[child_col].dropna()
    parent_ids = set(parent[parent_col].dropna().unique())
    orphans = child_ids[~child_ids.isin(parent_ids)]
    return {
        "column_present": True,
        "parent_column_present": True,
        "n_checked": int(len(child_ids)),
        "n_orphan": int(orphans.nunique()),
        "n_orphan_rows": int(len(orphans)),
    }


def _order_date_checks(orders: pd.DataFrame) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if "order_purchase_timestamp" not in orders.columns:
        checks.append(
            _check(
                "dates:purchase_present",
                False,
                "Falta order_purchase_timestamp en pedidos.",
            )
        )
        return checks

    purchase = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    n_bad_purchase = int(purchase.isna().sum())
    checks.append(
        _check(
            "dates:purchase_parseable",
            n_bad_purchase == 0,
            f"Timestamps de compra no parseables: {n_bad_purchase}.",
            details={"n_invalid": n_bad_purchase},
        )
    )

    if "order_approved_at" in orders.columns:
        approved = pd.to_datetime(orders["order_approved_at"], errors="coerce")
        mask = purchase.notna() & approved.notna() & (approved < purchase)
        n_bad = int(mask.sum())
        checks.append(
            _check(
                "dates:approved_after_purchase",
                n_bad == 0,
                f"Pedidos con aprobación anterior a la compra: {n_bad}.",
                details={"n_invalid": n_bad},
            )
        )

    if "order_delivered_customer_date" in orders.columns:
        delivered = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")
        mask = purchase.notna() & delivered.notna() & (delivered < purchase)
        n_bad = int(mask.sum())
        checks.append(
            _check(
                "dates:delivered_after_purchase",
                n_bad == 0,
                f"Pedidos con entrega anterior a la compra: {n_bad}.",
                details={"n_invalid": n_bad},
            )
        )
    return checks


def validate_dataset_directory(data_dir: Path) -> dict[str, Any]:
    """
    Valida catálogo Olist: archivos, claves, FKs, fechas y definición de venta.
    """
    tables = load_olist_tables(data_dir)
    catalog = {spec.file_name: spec for spec in expected_olist_tables()}
    found_names = set(tables)
    expected_names = set(catalog)
    missing = sorted(expected_names - found_names)

    checks: list[dict[str, Any]] = []
    if missing:
        checks.append(
            _check(
                "catalog:expected_files",
                False,
                f"Faltan {len(missing)} archivo(s) Olist esperados.",
                details={"missing": missing},
            )
        )
    else:
        checks.append(
            _check(
                "catalog:expected_files",
                True,
                "Las 9 tablas Olist esperadas están presentes.",
            )
        )

    for spec in expected_olist_tables():
        if spec.file_name not in tables:
            continue
        df = tables[spec.file_name]
        pk = _primary_key_check(df, spec.primary_key)
        severity = "warning" if spec.file_name in PK_WARNING_ONLY_FILES else "error"
        checks.append(
            _check(
                f"pk:{spec.file_name}",
                pk["is_unique"],
                (
                    f"Clave {spec.primary_key} única."
                    if pk["is_unique"]
                    else f"Clave {spec.primary_key} no única "
                    f"(duplicados={pk['n_duplicate_keys']}, nulos={pk.get('n_null_key_rows')})."
                ),
                severity=severity,
                details=pk,
            )
        )

        for child_col, parent_ref in spec.foreign_keys.items():
            parent_file, parent_col = _parent_ref(parent_ref)
            if parent_file not in tables:
                checks.append(
                    _check(
                        f"fk:{spec.file_name}.{child_col}",
                        False,
                        f"No se puede validar FK: falta {parent_file}.",
                    )
                )
                continue
            fk = _foreign_key_check(df, child_col, tables[parent_file], parent_col)
            n_orphan = fk.get("n_orphan")
            passed = n_orphan == 0
            checks.append(
                _check(
                    f"fk:{spec.file_name}.{child_col}",
                    passed,
                    (
                        f"FK {child_col} → {parent_ref} sin huérfanos."
                        if passed
                        else f"FK {child_col} → {parent_ref}: {n_orphan} valores huérfanos."
                    ),
                    details=fk,
                )
            )

    orders = tables.get("olist_orders_dataset.csv")
    status_counts: dict[str, int] = {}
    if orders is not None and "order_status" in orders.columns:
        status_counts = {str(k): int(v) for k, v in orders["order_status"].value_counts().items()}
        n_valid = int(orders["order_status"].isin(VALID_SALE_STATUSES).sum())
        checks.append(
            _check(
                "sale:valid_status_present",
                n_valid > 0,
                f"Pedidos con venta válida ({sorted(VALID_SALE_STATUSES)}): {n_valid}.",
                details={"n_valid_sale_orders": n_valid, "n_orders": int(len(orders))},
            )
        )
        checks.extend(_order_date_checks(orders))

    failed = [c for c in checks if not c["passed"] and c["severity"] == "error"]
    warned = [c for c in checks if not c["passed"] and c["severity"] == "warning"]

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "data_directory": str(data_dir.resolve()),
        "sale_definition": SALE_DEFINITION,
        "order_status_counts": status_counts,
        "tables_loaded": sorted(tables),
        "checks": checks,
        "summary": {
            "csv_files_found": len(found_names),
            "expected_tables_total": len(expected_names),
            "expected_tables_present": len(expected_names & found_names),
            "missing_expected_files": missing,
            "checks_total": len(checks),
            "checks_failed": len(failed),
            "checks_warned": len(warned),
            "passed": len(failed) == 0,
        },
    }


def validate_and_write_report(
    data_dir: Path, output_dir: Path
) -> tuple[dict[str, Any], Path, Path]:
    payload = validate_dataset_directory(data_dir)
    json_path, md_path = write_quality_report(payload, output_dir)
    return payload, json_path, md_path


__all__ = [
    "validate_and_write_report",
    "validate_dataset_directory",
]

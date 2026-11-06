"""KPIs comerciales sobre la tabla analítica (Fase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from smartstore.common.business_rules import SALE_DEFINITION
from smartstore.ingestion.transform import ENRICHED_FILENAME

REQUIRED_COLUMNS: tuple[str, ...] = (
    "order_id",
    "is_valid_sale",
    "price",
    "freight_value",
    "purchase_year",
    "purchase_week",
    "product_category_name",
    "product_category_name_english",
    "customer_state",
    "seller_id",
)


class EnrichedTableError(FileNotFoundError):
    """No está la tabla analítica o le faltan columnas."""


def enriched_table_path(processed_dir: Path) -> Path:
    return processed_dir / ENRICHED_FILENAME


def load_enriched_table(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise EnrichedTableError(
            f"No existe {path}. Ejecuta `smartstore build` antes de `smartstore analyze`."
        )
    frame = pd.read_csv(path)
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        raise EnrichedTableError(
            "A la tabla analítica le faltan columnas: " + ", ".join(missing)
        )
    return frame


def _as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _money(value: float) -> float:
    return round(float(value), 2)


def _category_label(frame: pd.DataFrame) -> pd.Series:
    english = frame["product_category_name_english"].astype("string")
    portuguese = frame["product_category_name"].astype("string")
    label = english.fillna(portuguese)
    return label.fillna("sin_categoria")


def _aggregate(sales: pd.DataFrame, keys: list[str]) -> list[dict[str, Any]]:
    if sales.empty:
        return []
    grouped = (
        sales.groupby(keys, dropna=False)
        .agg(
            orders=("order_id", "nunique"),
            items=("order_id", "size"),
            revenue=("price", "sum"),
            freight=("freight_value", "sum"),
        )
        .reset_index()
    )
    records: list[dict[str, Any]] = []
    for row in grouped.itertuples(index=False):
        record = {key: getattr(row, key) for key in keys}
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif hasattr(value, "item"):
                record[key] = value.item()
        record["orders"] = int(row.orders)
        record["items"] = int(row.items)
        record["revenue"] = _money(row.revenue)
        record["freight"] = _money(row.freight)
        records.append(record)
    return records


def compute_commercial_metrics(
    frame: pd.DataFrame,
    *,
    top_n: int = 15,
) -> dict[str, Any]:
    """
    Métricas solo sobre `is_valid_sale`.

    Ingreso = suma de `price` a nivel ítem. El flete se informa aparte y no entra
    en el ticket promedio.
    """
    working = frame.copy()
    working["is_valid_sale"] = _as_bool(working["is_valid_sale"])
    working["price"] = pd.to_numeric(working["price"], errors="coerce").fillna(0.0)
    working["freight_value"] = pd.to_numeric(
        working["freight_value"], errors="coerce"
    ).fillna(0.0)
    working["purchase_year"] = pd.to_numeric(working["purchase_year"], errors="coerce")
    working["purchase_week"] = pd.to_numeric(working["purchase_week"], errors="coerce")

    sales = working.loc[working["is_valid_sale"]].copy()
    sales["category"] = _category_label(sales)

    orders = int(sales["order_id"].nunique()) if not sales.empty else 0
    items = int(len(sales))
    revenue = float(sales["price"].sum()) if not sales.empty else 0.0
    freight = float(sales["freight_value"].sum()) if not sales.empty else 0.0

    weekly = _aggregate(sales, ["purchase_year", "purchase_week"])
    weekly.sort(key=lambda row: (row["purchase_year"] or 0, row["purchase_week"] or 0))

    by_category = _aggregate(sales, ["category"])
    by_category.sort(key=lambda row: (-row["revenue"], row["category"] or ""))

    by_state = _aggregate(sales, ["customer_state"])
    by_state.sort(key=lambda row: (-row["revenue"], str(row["customer_state"])))

    by_seller = _aggregate(sales, ["seller_id"])
    by_seller.sort(key=lambda row: (-row["revenue"], str(row["seller_id"])))

    return {
        "sale_definition": SALE_DEFINITION,
        "summary": {
            "lines_total": int(len(working)),
            "lines_valid": items,
            "lines_excluded": int(len(working) - items),
            "orders_valid": orders,
            "revenue": _money(revenue),
            "freight": _money(freight),
            "average_order_value": _money(revenue / orders) if orders else 0.0,
            "items_per_order": round(items / orders, 2) if orders else 0.0,
        },
        "weekly_demand": weekly,
        "by_category": by_category,
        "by_state": by_state,
        "by_seller": by_seller[:top_n],
    }

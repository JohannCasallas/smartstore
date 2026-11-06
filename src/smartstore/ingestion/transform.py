from __future__ import annotations

from pathlib import Path

import pandas as pd

from smartstore.common.business_rules import (
    ANALYTICAL_CORE_FILES,
    CATEGORY_TRANSLATION_FILE,
    VALID_SALE_STATUSES,
)
from smartstore.ingestion.loaders import load_olist_tables

ENRICHED_FILENAME = "order_items_enriched.csv"

OUTPUT_COLUMNS: tuple[str, ...] = (
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "customer_id",
    "order_status",
    "is_valid_sale",
    "order_purchase_timestamp",
    "purchase_year",
    "purchase_week",
    "order_approved_at",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
    "price",
    "freight_value",
    "product_category_name",
    "product_category_name_english",
    "customer_city",
    "customer_state",
    "customer_zip_code_prefix",
    "seller_city",
    "seller_state",
)


class MissingCoreTablesError(FileNotFoundError):
    """Faltan CSV imprescindibles para la tabla analítica."""


def missing_core_tables(tables: dict[str, pd.DataFrame]) -> list[str]:
    return [name for name in ANALYTICAL_CORE_FILES if name not in tables]


def build_order_items_enriched(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Tabla analítica a granularidad línea de pedido (order_id + order_item_id).

    No une pagos ni reseñas: romperían la granularidad o filtrarían el futuro.
    """
    missing = missing_core_tables(tables)
    if missing:
        raise MissingCoreTablesError(
            "Faltan tablas núcleo para la tabla analítica: " + ", ".join(missing)
        )

    items = tables["olist_order_items_dataset.csv"]
    orders = tables["olist_orders_dataset.csv"]
    products = tables["olist_products_dataset.csv"]
    customers = tables["olist_customers_dataset.csv"]
    sellers = tables["olist_sellers_dataset.csv"]

    frame = items.merge(orders, on="order_id", how="left", validate="many_to_one")
    frame = frame.merge(products, on="product_id", how="left", validate="many_to_one")
    frame = frame.merge(customers, on="customer_id", how="left", validate="many_to_one")
    frame = frame.merge(sellers, on="seller_id", how="left", validate="many_to_one")

    translation = tables.get(CATEGORY_TRANSLATION_FILE)
    if translation is not None and "product_category_name" in frame.columns:
        frame = frame.merge(
            translation,
            on="product_category_name",
            how="left",
            validate="many_to_one",
        )

    purchase = pd.to_datetime(frame["order_purchase_timestamp"], errors="coerce")
    iso = purchase.dt.isocalendar()
    frame["is_valid_sale"] = frame["order_status"].isin(VALID_SALE_STATUSES)
    frame["purchase_year"] = iso.year.astype("Int64")
    frame["purchase_week"] = iso.week.astype("Int64")

    for column in OUTPUT_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA

    return frame.loc[:, list(OUTPUT_COLUMNS)]


def build_processed_table(data_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, Path]:
    tables = load_olist_tables(data_dir)
    frame = build_order_items_enriched(tables)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / ENRICHED_FILENAME
    frame.to_csv(path, index=False)
    return frame, path

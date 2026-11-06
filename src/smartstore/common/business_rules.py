"""Reglas de negocio versionadas (ver ADR 0002)."""

from __future__ import annotations

# Pedido cerrado y entregado al cliente. Única etiqueta que cuenta como venta.
VALID_SALE_STATUSES: frozenset[str] = frozenset({"delivered"})

# Tablas cuya clave primaria en Olist no es estrictamente única en la práctica.
PK_WARNING_ONLY_FILES: frozenset[str] = frozenset(
    {
        "olist_order_reviews_dataset.csv",
        "olist_geolocation_dataset.csv",
    }
)

# Núcleo mínimo para construir la tabla analítica a granularidad ítem.
ANALYTICAL_CORE_FILES: tuple[str, ...] = (
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
)

CATEGORY_TRANSLATION_FILE = "product_category_name_translation.csv"

ORDER_DATETIME_COLUMNS: tuple[str, ...] = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)

SALE_DEFINITION = {
    "valid_statuses": sorted(VALID_SALE_STATUSES),
    "demand_timestamp": "order_purchase_timestamp",
    "line_amount_columns": ["price", "freight_value"],
    "adr": "docs/decisions/0002-definicion-de-venta.md",
}

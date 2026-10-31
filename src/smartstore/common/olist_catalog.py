from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OlistTableSpec:
    """Metadatos mínimos de una tabla Olist para validación en ingesta."""

    file_name: str
    description: str
    primary_key: tuple[str, ...]
    foreign_keys: dict[str, str]
    notes: str = ""


def expected_olist_tables() -> tuple[OlistTableSpec, ...]:
    """
    Inventario acordado con el Documento Maestro (Brazilian E-Commerce / Olist).

    Las claves son orientativas para perfilado; la granularidad final se confirma
    tras inspeccionar cardinalidades en el informe de calidad.
    """
    return (
        OlistTableSpec(
            file_name="olist_orders_dataset.csv",
            description="Pedidos: fechas y estados del ciclo de vida.",
            primary_key=("order_id",),
            foreign_keys={"customer_id": "olist_customers_dataset.customer_id"},
            notes="Definir qué order_status cuentan como venta válida antes de KPIs.",
        ),
        OlistTableSpec(
            file_name="olist_order_items_dataset.csv",
            description="Líneas de pedido: producto, precio y flete por artículo.",
            primary_key=("order_id", "order_item_id"),
            foreign_keys={
                "order_id": "olist_orders_dataset.order_id",
                "product_id": "olist_products_dataset.product_id",
                "seller_id": "olist_sellers_dataset.seller_id",
            },
            notes="Un pedido puede tener varias filas; no duplicar ingresos al unir.",
        ),
        OlistTableSpec(
            file_name="olist_products_dataset.csv",
            description="Atributos y categoría de productos.",
            primary_key=("product_id",),
            foreign_keys={},
            notes="Hay categorías y campos con valores faltantes.",
        ),
        OlistTableSpec(
            file_name="olist_customers_dataset.csv",
            description="Clientes (identificadores anonimizados).",
            primary_key=("customer_id",),
            foreign_keys={},
            notes="No usar para reidentificación; solo agregaciones.",
        ),
        OlistTableSpec(
            file_name="olist_sellers_dataset.csv",
            description="Vendedores del marketplace.",
            primary_key=("seller_id",),
            foreign_keys={},
            notes="No equivale a inventario operativo por vendedor.",
        ),
        OlistTableSpec(
            file_name="olist_order_payments_dataset.csv",
            description="Pagos asociados a pedidos.",
            primary_key=("order_id", "payment_sequential"),
            foreign_keys={"order_id": "olist_orders_dataset.order_id"},
            notes="Un pedido puede tener varios pagos; cuidado al sumar montos con joins.",
        ),
        OlistTableSpec(
            file_name="olist_order_reviews_dataset.csv",
            description="Reseñas y puntuaciones.",
            primary_key=("review_id",),
            foreign_keys={"order_id": "olist_orders_dataset.order_id"},
            notes="No usar fechas de reseña para predecir demanda pasada (fuga temporal).",
        ),
        OlistTableSpec(
            file_name="olist_geolocation_dataset.csv",
            description="Códigos postales y coordenadas.",
            primary_key=("geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"),
            foreign_keys={},
            notes="Tabla de referencia geográfica; cardinalidad alta.",
        ),
        OlistTableSpec(
            file_name="product_category_name_translation.csv",
            description="Traducción de nombres de categoría (PT → EN).",
            primary_key=("product_category_name",),
            foreign_keys={},
            notes="Útil para reportes en español/inglés.",
        ),
    )

# ADR 0003: KPIs comerciales

## Contexto

La tabla `order_items_enriched` ya marca la venta válida. Los indicadores de la
Fase 3 tienen que usar esa misma regla, sin volver a unir pagos ni reseñas.

## Decisión

- Universo: filas con `is_valid_sale = true`.
- **Ingreso:** suma de `price`.
- **Flete:** suma de `freight_value`, informado aparte. No entra en el ticket.
- **Ticket promedio:** ingreso / pedidos distintos (`order_id`).
- **Demanda semanal:** `purchase_year` + `purchase_week` (ISO de
  `order_purchase_timestamp`), con pedidos, ítems, ingreso y flete.
- Categoría de reporte: `product_category_name_english`, y si falta, el nombre
  en portugués o `sin_categoria`.

## Consecuencias

- El ingreso no coincide con la suma de `payment_value`.
- La serie semanal es la entrada de la Fase 4 (pronóstico).
- `smartstore analyze` materializa el informe en `docs/reports/`.

## Estado

Aceptado — 2026-11-05

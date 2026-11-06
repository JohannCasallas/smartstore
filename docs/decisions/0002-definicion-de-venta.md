# ADR 0002: Definición de venta y `order_status` válidos

## Contexto

Los KPIs, la tabla analítica y el pronóstico de demanda no pueden construirse mientras
`order_status` mezcle pedidos completados, en tránsito y anulados. Unir pagos o reseñas
sin esta regla duplica montos o introduce fuga temporal.

## Decisión

- **Venta válida:** pedido con `order_status = delivered`.
- **Fecha de la demanda:** `order_purchase_timestamp` (intención de compra), no la fecha
  de entrega ni de reseña.
- **Métrica de línea:** `price` y `freight_value` en `olist_order_items_dataset`
  (granularidad ítem). No sumar `payment_value` sobre un join a ítems.
- **Excluidos de venta:** `canceled`, `unavailable` y el resto de estados
  (`created`, `approved`, `invoiced`, `processing`, `shipped`, …). Siguen en el informe
  de calidad para auditoría.
- **No usar en demanda:** `review_*`, fechas de entrega al cliente, ni cualquier
  variable posterior a la compra.

La bandera `is_valid_sale` se materializa en `data/processed/order_items_enriched.csv`.

## Consecuencias

- El volumen de “ventas” será menor que el de pedidos totales (Olist incluye cancelados).
- Cambiar el conjunto de estados exige un ADR nuevo; no se decide en un notebook.
- `smartstore validate` y `smartstore build` leen esta regla desde
  `smartstore.common.business_rules`.

## Estado

Aceptado — 2026-10-31

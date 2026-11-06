# Diccionario de datos

Convenciones y columnas del dataset Olist. La **definición de venta** está en
[ADR 0002](../decisions/0002-definicion-de-venta.md). Completar nulos y cardinalidades
reales tras `smartstore profile` y `smartstore validate` sobre `data/raw/`.

## Convenciones

- **Granularidad analítica:** una fila = un ítem de pedido (`order_id` + `order_item_id`).
- **Venta válida:** `order_status = delivered`.
- **Fecha de demanda:** `order_purchase_timestamp`.
- **No unir a la fact table:** pagos (varios por pedido) ni reseñas (fuga temporal).

---

## olist_orders_dataset

Granularidad: un pedido. PK: `order_id`. FK: `customer_id` → customers.

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| order_id | str | Identificador del pedido | Clave primaria |
| customer_id | str | Cliente del pedido | Cambia por pedido; no es `customer_unique_id` |
| order_status | str | Estado del ciclo de vida | Solo `delivered` cuenta como venta |
| order_purchase_timestamp | datetime | Compra | Reloj de la demanda |
| order_approved_at | datetime | Aprobación de pago | Puede ser nulo |
| order_delivered_carrier_date | datetime | Entrega al transportista | Posterior a la compra; no usar para demand forecast |
| order_delivered_customer_date | datetime | Entrega al cliente | Posterior; no usar para demand forecast |
| order_estimated_delivery_date | datetime | ETA prometida | |

---

## olist_order_items_dataset

Granularidad: línea de pedido. PK: (`order_id`, `order_item_id`).

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| order_id | str | Pedido | FK → orders |
| order_item_id | int | Número de línea dentro del pedido | Empieza en 1 |
| product_id | str | Producto | FK → products |
| seller_id | str | Vendedor | FK → sellers |
| shipping_limit_date | datetime | Límite de despacho | |
| price | float | Precio del ítem | Base de ingresos de línea |
| freight_value | float | Flete del ítem | No mezclar con `payment_value` |

---

## olist_products_dataset

Granularidad: producto. PK: `product_id`.

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| product_id | str | Producto | |
| product_category_name | str | Categoría en portugués | Puede ser nulo; unir traducción |
| product_name_lenght | int | Longitud del nombre | Typo original `lenght` |
| product_description_lenght | int | Longitud de la descripción | Typo original `lenght` |
| product_photos_qty | int | Cantidad de fotos | |
| product_weight_g | float | Peso (g) | |
| product_length_cm | float | Largo (cm) | |
| product_height_cm | float | Alto (cm) | |
| product_width_cm | float | Ancho (cm) | |

---

## olist_customers_dataset

Granularidad: `customer_id` (por pedido). PK: `customer_id`.

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| customer_id | str | Id de cliente en el pedido | |
| customer_unique_id | str | Persona a lo largo de pedidos | Usar para recurrencia, no como PK de esta tabla |
| customer_zip_code_prefix | int | Prefijo postal | |
| customer_city | str | Ciudad | |
| customer_state | str | Estado (UF) | |

---

## olist_sellers_dataset

Granularidad: vendedor. PK: `seller_id`.

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| seller_id | str | Vendedor | |
| seller_zip_code_prefix | int | Prefijo postal | |
| seller_city | str | Ciudad | |
| seller_state | str | Estado (UF) | |

---

## olist_order_payments_dataset

Granularidad: intento/medio de pago. PK: (`order_id`, `payment_sequential`).

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| order_id | str | Pedido | Un pedido puede tener varios pagos |
| payment_sequential | int | Orden del pago | |
| payment_type | str | Medio | credit_card, boleto, voucher, … |
| payment_installments | int | Cuotas | |
| payment_value | float | Monto del pago | No unir a ítems para sumar ingresos |

---

## olist_order_reviews_dataset

Granularidad: reseña. PK declarada: `review_id` (en Olist puede repetirse).

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| review_id | str | Reseña | Unicidad no estricta; aviso en validate |
| order_id | str | Pedido | FK → orders |
| review_score | int | Puntuación 1–5 | Posterior a la compra |
| review_comment_title | str | Título | Nulos frecuentes |
| review_comment_message | str | Comentario | Nulos frecuentes |
| review_creation_date | datetime | Alta de la reseña | No usar como fecha de demanda |
| review_answer_timestamp | datetime | Respuesta | |

---

## olist_geolocation_dataset

Granularidad: coordenada por prefijo postal (no única por ZIP).

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| geolocation_zip_code_prefix | int | Prefijo | Varias filas por prefijo |
| geolocation_lat | float | Latitud | |
| geolocation_lng | float | Longitud | |
| geolocation_city | str | Ciudad | |
| geolocation_state | str | Estado | |

---

## product_category_name_translation

Granularidad: categoría. PK: `product_category_name`.

| Columna | Tipo | Descripción | Notas |
|---------|------|-------------|-------|
| product_category_name | str | Nombre PT | |
| product_category_name_english | str | Nombre EN | Usar en reportes |

---

## order_items_enriched (procesado)

Salida de `smartstore build` en `data/processed/order_items_enriched.csv`.

Granularidad: línea de pedido. Incluye `is_valid_sale`, `purchase_year` y
`purchase_week` (ISO) derivados de `order_purchase_timestamp`.

`smartstore analyze` lee este archivo y publica KPIs en `docs/reports/analytics_*.md`.
El ingreso es la suma de `price` en filas con `is_valid_sale = true`. `freight_value`
se reporta aparte y no entra en el ticket promedio.

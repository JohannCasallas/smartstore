# Dataset Olist — Brazilian E-Commerce

## Fuente

- **Nombre:** Brazilian E-Commerce Public Dataset by Olist  
- **Plataforma:** [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
- **Uso en SmartStore:** caso de estudio histórico; no representa una tienda en tiempo real.

## Instalación en el proyecto

1. Descarga el archivo desde Kaggle (requiere cuenta; respeta los términos de la plataforma y del dataset).
2. Extrae los CSV en `data/raw/` **sin renombrar ni editar** los originales.
3. Ejecuta:

```bash
smartstore profile
```

4. Revisa el informe más reciente en `docs/reports/`.

## Archivos esperados

| Archivo | Dominio |
|---------|---------|
| `olist_orders_dataset.csv` | Pedidos |
| `olist_order_items_dataset.csv` | Líneas de pedido |
| `olist_products_dataset.csv` | Productos |
| `olist_customers_dataset.csv` | Clientes |
| `olist_sellers_dataset.csv` | Vendedores |
| `olist_order_payments_dataset.csv` | Pagos |
| `olist_order_reviews_dataset.csv` | Reseñas |
| `olist_geolocation_dataset.csv` | Geolocalización |
| `product_category_name_translation.csv` | Traducción de categorías |

## Precauciones (resumen)

- Definir qué `order_status` cuentan como venta antes de calcular ingresos.
- Al unir pagos o ítems, respetar granularidad para no duplicar montos.
- No usar variables posteriores al evento (reseñas, entrega) para pronosticar demanda pasada.

Atribución: incluir en README y en entregables públicos la referencia a Olist/Kaggle según exijan los términos vigentes del dataset.

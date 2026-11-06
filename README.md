# SmartStore

Plataforma de analítica comercial y pronóstico de demanda con Python, orientada a un flujo reproducible: **ingestión → calidad → analítica → pronóstico → inventario simulado**.

Dataset inicial: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## Requisitos

- Python **3.12+**
- Git
- Windows + VS Code (entorno de referencia del proyecto)

## Instalación

```powershell
cd C:\Proyectos\smartstore
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

## Uso — Fases 1 a 3

1. Coloca los CSV de Olist en `data/raw/` (sin modificar originales).
2. Perfila, valida, construye la tabla analítica y calcula KPIs:

```powershell
smartstore profile
smartstore validate
smartstore build
smartstore analyze
```

- `profile` / `validate` / `analyze` escriben JSON + Markdown en `docs/reports/`.
- `build` escribe `data/processed/order_items_enriched.csv` (una fila por ítem;
  `is_valid_sale` según [ADR 0002](docs/decisions/0002-definicion-de-venta.md)).
- `analyze` usa solo ventas válidas: ingreso = suma de `price`; flete aparte;
  demanda semanal ISO en el informe.
- Código de salida `2` si faltan archivos Olist, hay chequeos de calidad fallidos
  o no existe la tabla analítica.

Documentación: [docs/README.md](docs/README.md).

## Desarrollo

```powershell
python -m pytest
python -m ruff check src tests
```

## Estructura

```
smartstore/
├── data/raw|interim|processed/
├── docs/                    # Diccionario, decisiones, informes generados
├── src/smartstore/
│   ├── common/              # Rutas y catálogo Olist
│   ├── ingestion/           # Perfilado, validación y tabla analítica
│   ├── analytics/           # KPIs y demanda semanal (Fase 3)
│   ├── forecasting/         # (Fase 4)
│   └── inventory/           # (Fase 5)
└── tests/
```

## Licencia del dataset

Usa Olist/Kaggle según sus términos; no subas CSV grandes al repositorio.

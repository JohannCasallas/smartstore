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

## Uso — Fase 1 (perfilado)

1. Coloca los CSV de Olist en `data/raw/` (sin modificar originales).
2. Genera el informe:

```powershell
smartstore profile
```

Salida en `docs/reports/` (JSON + Markdown). Código de salida `2` si faltan archivos esperados del dataset.

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
│   ├── ingestion/           # Perfilado y reportes
│   ├── analytics/           # (Fase 3)
│   ├── forecasting/         # (Fase 4)
│   └── inventory/           # (Fase 5)
└── tests/
```

## Licencia del dataset

Usa Olist/Kaggle según sus términos; no subas CSV grandes al repositorio.

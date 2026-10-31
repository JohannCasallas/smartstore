# ADR 0001: Layout `src/` y CLI de perfilado

## Contexto

SmartStore debe ser reproducible por cualquier persona que clone el repo. La Fase 1 exige perfilar Olist y dejar evidencia verificable (informe), no scripts sueltos en la raíz.

## Decisión

- Código en `src/smartstore/` con paquetes `common`, `ingestion` y módulos futuros (`analytics`, `forecasting`, `inventory`).
- Rutas del proyecto resueltas desde `pyproject.toml` (`get_paths()`).
- Comando `smartstore profile` genera JSON + Markdown en `docs/reports/`.
- Catálogo Olist en código (`olist_catalog.py`) alineado con el Documento Maestro.

## Consecuencias

- Instalación editable obligatoria (`pip install -e .`) para usar el comando `smartstore`.
- Los informes timestamped pueden acumularse; limpiar o archivar manualmente si hace falta.

## Estado

Aceptado — 2026-10-10

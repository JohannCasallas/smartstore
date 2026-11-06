"""Indicadores y análisis comercial (Fase 3)."""

from smartstore.analytics.metrics import (
    EnrichedTableError,
    compute_commercial_metrics,
    load_enriched_table,
)
from smartstore.analytics.report import build_analytics_markdown, write_analytics_report

__all__ = [
    "EnrichedTableError",
    "build_analytics_markdown",
    "compute_commercial_metrics",
    "load_enriched_table",
    "write_analytics_report",
]

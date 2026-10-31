"""Utilidades y configuración compartidas."""

from smartstore.common.config import ProjectPaths, get_paths
from smartstore.common.olist_catalog import OlistTableSpec, expected_olist_tables

__all__ = [
    "OlistTableSpec",
    "ProjectPaths",
    "expected_olist_tables",
    "get_paths",
]

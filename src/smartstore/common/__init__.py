"""Utilidades y configuración compartidas."""

from smartstore.common.business_rules import SALE_DEFINITION, VALID_SALE_STATUSES
from smartstore.common.config import ProjectPaths, get_paths
from smartstore.common.olist_catalog import OlistTableSpec, expected_olist_tables

__all__ = [
    "OlistTableSpec",
    "ProjectPaths",
    "SALE_DEFINITION",
    "VALID_SALE_STATUSES",
    "expected_olist_tables",
    "get_paths",
]

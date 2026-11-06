from __future__ import annotations

from pathlib import Path

import pandas as pd

from smartstore.common.business_rules import ORDER_DATETIME_COLUMNS
from smartstore.common.olist_catalog import expected_olist_tables


def load_csv(path: Path) -> pd.DataFrame:
    """Lee un CSV Olist; parsea fechas de pedidos si aplican."""
    parse_dates = [c for c in ORDER_DATETIME_COLUMNS]
    header = pd.read_csv(path, nrows=0)
    dates = [c for c in parse_dates if c in header.columns]
    if dates:
        return pd.read_csv(path, parse_dates=dates)
    return pd.read_csv(path)


def load_olist_tables(data_dir: Path) -> dict[str, pd.DataFrame]:
    """Carga los CSV presentes cuyo nombre está en el catálogo Olist."""
    expected = {spec.file_name for spec in expected_olist_tables()}
    tables: dict[str, pd.DataFrame] = {}
    for name in sorted(expected):
        path = data_dir / name
        if path.is_file():
            tables[name] = load_csv(path)
    return tables

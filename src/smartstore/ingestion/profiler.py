from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from smartstore.common.olist_catalog import OlistTableSpec, expected_olist_tables
from smartstore.ingestion.report import write_profile_report


def _catalog_by_filename() -> dict[str, OlistTableSpec]:
    return {spec.file_name: spec for spec in expected_olist_tables()}


def _primary_key_check(df: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for col in columns:
        if col not in df.columns:
            result[col] = {
                "present": False,
                "n_unique": None,
                "n_null": None,
                "is_unique": False,
            }
            continue
        series = df[col]
        n_null = int(series.isna().sum())
        n_unique = int(series.nunique(dropna=True))
        result[col] = {
            "present": True,
            "n_unique": n_unique,
            "n_null": n_null,
            "is_unique": n_null == 0 and n_unique == len(df),
        }
    return result


def profile_csv(csv_path: Path, *, catalog: OlistTableSpec | None = None) -> dict[str, Any]:
    """
    Genera un perfil de un archivo CSV: volumen, tipos, nulos, duplicados y claves.

    Args:
        csv_path: Ruta del archivo CSV.
        catalog: Metadatos Olist opcionales para validar columnas de clave.

    Returns:
        Diccionario serializable con métricas de calidad del archivo.
    """
    df = pd.read_csv(csv_path)
    rows = len(df)
    missing = df.isna().sum()
    missing_pct = (missing / rows * 100).round(4) if rows else missing * 0

    profile: dict[str, Any] = {
        "file_name": csv_path.name,
        "file_path": str(csv_path.resolve()),
        "file_size_bytes": csv_path.stat().st_size,
        "rows": rows,
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": missing.astype(int).to_dict(),
        "missing_pct": missing_pct.astype(float).to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }

    if catalog is not None:
        profile["catalog_match"] = {
            "description": catalog.description,
            "primary_key": list(catalog.primary_key),
            "foreign_keys": catalog.foreign_keys,
            "notes": catalog.notes,
        }
        profile["primary_key_check"] = _primary_key_check(df, catalog.primary_key)

    return profile


def profile_csv_legacy(csv_path: Path) -> dict[str, Any]:
    """Compatibilidad con la API inicial de perfilado (sin catálogo Olist)."""
    p = profile_csv(csv_path)
    return {
        "file_size_bytes": p["file_size_bytes"],
        "file_name": p["file_name"],
        "rows": p["rows"],
        "columns": p["columns"],
        "column_names": p["column_names"],
        "data_types": p["data_types"],
        "missing_values": p["missing_values"],
        "duplicate_rows": p["duplicate_rows"],
    }


def profile_directory(data_dir: Path) -> list[dict[str, Any]]:
    """
    Perfiles todos los CSV de una carpeta (API simple, sin metadatos Olist).

    Returns:
        Lista de perfiles en orden alfabético por nombre de archivo.
    """
    catalog = _catalog_by_filename()
    profiles = []
    for csv_file in sorted(data_dir.glob("*.csv")):
        spec = catalog.get(csv_file.name)
        if spec is not None:
            profiles.append(profile_csv(csv_file, catalog=spec))
        else:
            profiles.append(profile_csv_legacy(csv_file))
    return profiles


def profile_dataset_directory(data_dir: Path) -> dict[str, Any]:
    """
    Perfilado completo para Fase 1: archivos encontrados vs inventario Olist esperado.
    """
    catalog = _catalog_by_filename()
    found_names = {p.name for p in data_dir.glob("*.csv")}
    expected_names = set(catalog.keys())
    missing = sorted(expected_names - found_names)
    extra = sorted(found_names - expected_names)

    profiles: list[dict[str, Any]] = []
    for csv_file in sorted(data_dir.glob("*.csv")):
        spec = catalog.get(csv_file.name)
        profiles.append(profile_csv(csv_file, catalog=spec))

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "data_directory": str(data_dir.resolve()),
        "profiles": profiles,
        "summary": {
            "csv_files_found": len(profiles),
            "expected_tables_total": len(expected_names),
            "expected_tables_present": len(expected_names & found_names),
            "missing_expected_files": missing,
            "unexpected_files": extra,
        },
    }


__all__ = [
    "profile_csv",
    "profile_csv_legacy",
    "profile_directory",
    "profile_dataset_directory",
    "write_profile_report",
]

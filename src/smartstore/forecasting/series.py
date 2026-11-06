"""Serie semanal de demanda a partir de la tabla analítica."""

from __future__ import annotations

import pandas as pd


class ForecastError(ValueError):
    """La serie de demanda no alcanza para pronosticar."""


def week_start(year: int, week: int) -> pd.Timestamp:
    """Lunes de la semana ISO."""
    return pd.to_datetime(f"{int(year)}-W{int(week):02d}-1", format="%G-W%V-%u")


def weekly_item_demand(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Ítems vendidos por semana ISO.

    Una fila de venta válida cuenta como un ítem. Las semanas sin ventas,
    entre la primera y la última observadas, quedan en cero.
    """
    working = frame.copy()
    flag = working["is_valid_sale"]
    if flag.dtype != bool:
        flag = flag.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})
    working["is_valid_sale"] = flag
    sales = working.loc[working["is_valid_sale"]].copy()
    if sales.empty:
        raise ForecastError("No hay ventas válidas para armar la serie semanal.")

    sales["purchase_year"] = pd.to_numeric(sales["purchase_year"], errors="coerce")
    sales["purchase_week"] = pd.to_numeric(sales["purchase_week"], errors="coerce")
    sales = sales.dropna(subset=["purchase_year", "purchase_week"])
    if sales.empty:
        raise ForecastError("Las ventas válidas no tienen semana de compra.")

    grouped = (
        sales.groupby(["purchase_year", "purchase_week"], dropna=False)
        .size()
        .rename("items")
        .reset_index()
    )
    grouped["week_start"] = [
        week_start(year, week)
        for year, week in zip(grouped["purchase_year"], grouped["purchase_week"], strict=True)
    ]
    grouped = grouped.sort_values("week_start")

    full_index = pd.date_range(
        grouped["week_start"].min(),
        grouped["week_start"].max(),
        freq="W-MON",
    )
    series = grouped.set_index("week_start")["items"].reindex(full_index, fill_value=0)
    iso = series.index.isocalendar()
    return pd.DataFrame(
        {
            "week_start": series.index,
            "purchase_year": iso.year.astype(int).to_numpy(),
            "purchase_week": iso.week.astype(int).to_numpy(),
            "items": series.astype(int).to_numpy(),
        }
    )

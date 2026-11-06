"""Tres pronósticos de referencia y la elección del que menos se equivoca."""

from __future__ import annotations

from typing import Any

import pandas as pd

MODEL_LABELS: dict[str, str] = {
    "naive": "último valor",
    "moving_average": "promedio móvil de 4 semanas",
    "seasonal_naive": "misma semana del año anterior",
}

# Si empatan en error, gana el más simple.
_SIMPLICITY: dict[str, int] = {
    "naive": 0,
    "moving_average": 1,
    "seasonal_naive": 2,
}

SEASON_WEEKS = 52
MOVING_WINDOW = 4


def predict_next(history: list[float], model: str) -> float:
    """Un paso adelante usando solo el pasado."""
    if not history:
        return 0.0
    if model == "naive":
        return float(history[-1])
    if model == "moving_average":
        window = history[-MOVING_WINDOW:]
        return float(sum(window) / len(window))
    if model == "seasonal_naive":
        if len(history) >= SEASON_WEEKS:
            return float(history[-SEASON_WEEKS])
        return float(history[-1])
    raise ValueError(f"Modelo desconocido: {model}")


def project(history: list[float], model: str, horizon: int) -> list[float]:
    """Repite el pronóstico `horizon` veces. Cada predicción entra al historial."""
    extended = list(history)
    future: list[float] = []
    for _ in range(horizon):
        step = predict_next(extended, model)
        future.append(round(step, 2))
        extended.append(step)
    return future


def _mae(history: list[float], model: str, holdout: int) -> float:
    errors: list[float] = []
    start = len(history) - holdout
    for index in range(start, len(history)):
        predicted = predict_next(history[:index], model)
        errors.append(abs(history[index] - predicted))
    return sum(errors) / len(errors)


def backtest_horizon(n_weeks: int, requested: int) -> int:
    """Semanas finales reservadas para medir error, sin usarlas para elegir a ciegas."""
    if n_weeks < 2:
        return 0
    return max(1, min(requested, n_weeks // 2))


def select_baseline(
    items: list[float],
    *,
    horizon: int = 8,
) -> dict[str, Any]:
    """
    Compara los tres modelos en las últimas semanas y se queda con el menor MAE.

    El pronóstico futuro usa toda la serie, incluida la parte que sirvió para medir.
    """
    holdout = backtest_horizon(len(items), horizon)
    evaluations: list[dict[str, Any]] = []
    if holdout:
        for model in MODEL_LABELS:
            mae = round(_mae(items, model, holdout), 2)
            evaluations.append(
                {
                    "model": model,
                    "label": MODEL_LABELS[model],
                    "mae": mae,
                    "holdout_weeks": holdout,
                }
            )
        winner = min(evaluations, key=lambda row: (row["mae"], _SIMPLICITY[row["model"]]))
        chosen = winner["model"]
    else:
        chosen = "naive"

    return {
        "chosen_model": chosen,
        "chosen_label": MODEL_LABELS[chosen],
        "holdout_weeks": holdout,
        "evaluations": evaluations,
        "future_items": project(items, chosen, horizon),
    }


def future_weeks(last_week_start: pd.Timestamp, horizon: int) -> pd.DatetimeIndex:
    start = last_week_start + pd.Timedelta(weeks=1)
    return pd.date_range(start, periods=horizon, freq="W-MON")

import json
from pathlib import Path

import pandas as pd

from smartstore.cli import main
from smartstore.forecasting.baseline import select_baseline
from smartstore.forecasting.series import weekly_item_demand

OLIST_MINI = Path(__file__).parent / "fixtures" / "olist_mini"


def test_weekly_series_fills_missing_weeks() -> None:
    frame = pd.DataFrame(
        {
            "is_valid_sale": [True, True],
            "purchase_year": [2017, 2017],
            "purchase_week": [1, 3],
        }
    )
    series = weekly_item_demand(frame)
    assert list(series["purchase_week"]) == [1, 2, 3]
    assert list(series["items"]) == [1, 0, 1]


def test_seasonal_baseline_wins_on_a_repeated_pattern() -> None:
    pattern = [10, 20, 30, 40] * 16
    result = select_baseline(pattern, horizon=4)
    assert result["chosen_model"] == "seasonal_naive"
    assert result["future_items"] == [10.0, 20.0, 30.0, 40.0]


def test_tie_prefers_the_simpler_model() -> None:
    result = select_baseline([8.0] * 12, horizon=4)
    assert result["chosen_model"] == "naive"
    assert result["future_items"] == [8.0, 8.0, 8.0, 8.0]


def test_cli_forecast_on_mini_dataset(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    assert main(["build", "--data-dir", str(OLIST_MINI), "--output-dir", str(processed)]) == 0
    code = main(
        [
            "forecast",
            "--input",
            str(processed / "order_items_enriched.csv"),
            "--output-dir",
            str(reports),
            "--series-dir",
            str(processed),
            "--horizon",
            "4",
        ]
    )
    assert code == 0
    payload = json.loads(next(reports.glob("forecast_*.json")).read_text(encoding="utf-8"))
    assert payload["chosen_model"] == "naive"
    assert len(payload["forecast"]) == 4
    history = pd.read_csv(processed / "weekly_item_demand.csv")
    assert int(history["items"].sum()) == 2


def test_cli_forecast_missing_table(tmp_path: Path) -> None:
    code = main(
        [
            "forecast",
            "--input",
            str(tmp_path / "missing.csv"),
            "--output-dir",
            str(tmp_path / "reports"),
            "--series-dir",
            str(tmp_path),
        ]
    )
    assert code == 2

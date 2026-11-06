import json
from pathlib import Path

from smartstore.analytics.metrics import compute_commercial_metrics
from smartstore.cli import main
from smartstore.ingestion.loaders import load_olist_tables
from smartstore.ingestion.transform import build_order_items_enriched

OLIST_MINI = Path(__file__).parent / "fixtures" / "olist_mini"


def _sales_frame():
    return build_order_items_enriched(load_olist_tables(OLIST_MINI))


def test_kpis_use_only_delivered_lines() -> None:
    metrics = compute_commercial_metrics(_sales_frame())
    summary = metrics["summary"]

    assert summary["lines_total"] == 4
    assert summary["lines_valid"] == 2
    assert summary["lines_excluded"] == 2
    assert summary["orders_valid"] == 1
    assert summary["revenue"] == 150.0
    assert summary["freight"] == 15.0
    assert summary["average_order_value"] == 150.0
    assert summary["items_per_order"] == 2.0

    categories = {row["category"]: row["revenue"] for row in metrics["by_category"]}
    assert categories == {"health_beauty": 100.0, "computers_accessories": 50.0}
    assert metrics["by_state"][0]["customer_state"] == "SP"
    assert metrics["by_seller"][0]["seller_id"] == "s1"
    assert metrics["weekly_demand"][0]["purchase_year"] == 2017
    assert metrics["weekly_demand"][0]["purchase_week"] == 2
    assert metrics["weekly_demand"][0]["orders"] == 1


def test_cli_analyze_writes_report(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    assert main(["build", "--data-dir", str(OLIST_MINI), "--output-dir", str(processed)]) == 0

    code = main(
        [
            "analyze",
            "--input",
            str(processed / "order_items_enriched.csv"),
            "--output-dir",
            str(reports),
        ]
    )

    assert code == 0
    written = list(reports.glob("analytics_*.json"))
    assert len(written) == 1
    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert payload["summary"]["revenue"] == 150.0
    assert list(reports.glob("analytics_*.md"))


def test_cli_analyze_missing_table(tmp_path: Path) -> None:
    code = main(
        [
            "analyze",
            "--input",
            str(tmp_path / "order_items_enriched.csv"),
            "--output-dir",
            str(tmp_path / "reports"),
        ]
    )
    assert code == 2

from pathlib import Path

from smartstore.cli import main
from smartstore.ingestion.validate import validate_dataset_directory

OLIST_MINI = Path(__file__).parent / "fixtures" / "olist_mini"


def test_validate_olist_mini_passes() -> None:
    payload = validate_dataset_directory(OLIST_MINI)

    assert payload["summary"]["passed"] is True
    assert payload["summary"]["missing_expected_files"] == []
    assert payload["order_status_counts"]["delivered"] == 1
    assert payload["sale_definition"]["valid_statuses"] == ["delivered"]


def test_validate_detects_orphan_product(tmp_path: Path) -> None:
    for src in OLIST_MINI.glob("*.csv"):
        (tmp_path / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    items = tmp_path / "olist_order_items_dataset.csv"
    items.write_text(
        items.read_text(encoding="utf-8") + "o1,3,p_missing,s1,2017-01-12 00:00:00,9.0,1.0\n",
        encoding="utf-8",
    )

    payload = validate_dataset_directory(tmp_path)
    fk_id = "fk:olist_order_items_dataset.csv.product_id"
    fk = next(c for c in payload["checks"] if c["id"] == fk_id)

    assert fk["passed"] is False
    assert payload["summary"]["passed"] is False


def test_cli_validate_on_mini(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    code = main(["validate", "--data-dir", str(OLIST_MINI), "--output-dir", str(out)])

    assert code == 0
    assert list(out.glob("data_quality_*.md"))

from pathlib import Path

import pytest

from smartstore.cli import main
from smartstore.ingestion.loaders import load_olist_tables
from smartstore.ingestion.transform import MissingCoreTablesError, build_order_items_enriched

OLIST_MINI = Path(__file__).parent / "fixtures" / "olist_mini"


def test_enriched_table_grain_and_sale_flag() -> None:
    tables = load_olist_tables(OLIST_MINI)
    frame = build_order_items_enriched(tables)

    assert len(frame) == 4
    assert frame.duplicated(subset=["order_id", "order_item_id"]).sum() == 0
    assert int(frame["is_valid_sale"].sum()) == 2
    delivered = frame.loc[frame["order_id"] == "o1"]
    assert delivered["is_valid_sale"].all()
    assert set(delivered["product_category_name_english"]) <= {
        "health_beauty",
        "computers_accessories",
    }
    canceled = frame.loc[frame["order_id"] == "o2"]
    assert not canceled["is_valid_sale"].any()


def test_build_requires_core_tables() -> None:
    with pytest.raises(MissingCoreTablesError, match="olist_orders_dataset.csv"):
        build_order_items_enriched({})


def test_cli_build_writes_csv(tmp_path: Path) -> None:
    out = tmp_path / "processed"
    code = main(["build", "--data-dir", str(OLIST_MINI), "--output-dir", str(out)])

    assert code == 0
    csv_path = out / "order_items_enriched.csv"
    assert csv_path.is_file()
    text = csv_path.read_text(encoding="utf-8")
    assert "is_valid_sale" in text
    assert "purchase_week" in text

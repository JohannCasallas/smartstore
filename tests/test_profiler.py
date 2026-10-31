from pathlib import Path

from smartstore.ingestion.profiler import profile_csv, profile_dataset_directory

FIXTURES = Path(__file__).parent / "fixtures"


def test_profile_csv_counts_duplicates_and_nulls() -> None:
    path = FIXTURES / "sample_orders.csv"
    result = profile_csv(path)

    assert result["rows"] == 3
    assert result["duplicate_rows"] == 1
    assert result["missing_values"]["customer_id"] == 0


def test_profile_dataset_directory_flags_missing_olist_files(tmp_path: Path) -> None:
    sample = FIXTURES / "sample_orders.csv"
    (tmp_path / "olist_orders_dataset.csv").write_text(
        sample.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    payload = profile_dataset_directory(tmp_path)

    assert payload["summary"]["csv_files_found"] == 1
    assert payload["summary"]["expected_tables_present"] == 1
    assert len(payload["summary"]["missing_expected_files"]) == 8
    assert payload["profiles"][0]["file_name"] == "olist_orders_dataset.csv"

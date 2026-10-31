from smartstore.cli import main


def test_cli_profile_on_empty_raw(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "raw"
    data_dir.mkdir()
    out_dir = tmp_path / "reports"

    code = main(["profile", "--data-dir", str(data_dir), "--output-dir", str(out_dir)])

    assert code == 2
    assert list(out_dir.glob("data_profile_*.md"))

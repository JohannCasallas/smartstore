from smartstore.common.config import get_paths


def test_get_paths_finds_project_root() -> None:
    paths = get_paths()

    assert paths.data_raw.name == "raw"
    assert (paths.root / "pyproject.toml").is_file()
    assert paths.docs_reports == paths.docs / "reports"

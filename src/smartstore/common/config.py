from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _find_project_root(start: Path | None = None) -> Path:
    """Sube desde `start` (o cwd) hasta encontrar pyproject.toml."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return current


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    root: Path
    data_raw: Path
    data_interim: Path
    data_processed: Path
    docs: Path
    docs_reports: Path
    models: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        root = root.resolve()
        docs = root / "docs"
        return cls(
            root=root,
            data_raw=root / "data" / "raw",
            data_interim=root / "data" / "interim",
            data_processed=root / "data" / "processed",
            docs=docs,
            docs_reports=docs / "reports",
            models=root / "models",
        )


@lru_cache(maxsize=1)
def get_paths(start: Path | None = None) -> ProjectPaths:
    return ProjectPaths.from_root(_find_project_root(start))

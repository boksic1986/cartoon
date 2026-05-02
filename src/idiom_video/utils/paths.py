from __future__ import annotations

from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return Path.cwd().resolve()


def output_dir_for_slug(base_output_dir: str | Path, slug: str) -> Path:
    return ensure_dir(Path(base_output_dir) / slug)

from __future__ import annotations

import shutil
from pathlib import Path


def generate_cover(story_dir: str | Path) -> Path:
    story = Path(story_dir)
    final_dir = story / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    cover = final_dir / "cover_mock.png"
    first = next((story / "images_approved").glob("*.png"), None) if (story / "images_approved").exists() else None
    if first:
        shutil.copy2(first, cover)
    else:
        cover.write_text("No approved image available for cover.\n", encoding="utf-8")
    return cover

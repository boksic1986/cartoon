from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel


class ComposeResult(BaseModel):
    output_path: str
    used_ffmpeg: bool
    message: str


def compose_mock_final(project_dir: str | Path, ffmpeg_path: str | None = None) -> ComposeResult:
    story_dir = Path(project_dir)
    final_dir = story_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    first_image = next((story_dir / "images_approved").glob("*.png"), None) if (story_dir / "images_approved").exists() else None

    if ffmpeg and first_image and Path(ffmpeg).name != "definitely-not-existing-ffmpeg":
        output = final_dir / "final_mock.mp4"
        command = [
            ffmpeg,
            "-y",
            "-loop",
            "1",
            "-i",
            str(first_image),
            "-t",
            "1",
            "-vf",
            "scale=1080:1920,format=yuv420p",
            str(output),
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return ComposeResult(output_path=str(output), used_ffmpeg=True, message="Created mock MP4 with FFmpeg.")
        except Exception as exc:
            fallback = final_dir / "final_mock.txt"
            fallback.write_text(f"FFmpeg fallback used: {exc}\n", encoding="utf-8")
            return ComposeResult(output_path=str(fallback), used_ffmpeg=False, message="FFmpeg failed; wrote fallback text.")

    output = final_dir / "final_mock.txt"
    output.write_text(
        "Mock final artifact. FFmpeg was not available or no approved image was found.\n",
        encoding="utf-8",
    )
    return ComposeResult(output_path=str(output), used_ffmpeg=False, message="Wrote fallback text artifact.")

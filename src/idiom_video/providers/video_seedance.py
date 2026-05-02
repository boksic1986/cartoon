from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import VideoClip, VideoGenerationJob


class SeedanceVideoProvider:
    provider_name = "seedance"

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def generate(self, job: VideoGenerationJob) -> VideoClip:
        if not self.dry_run:
            raise NotImplementedError("Real Seedance API integration is deferred to a later milestone.")
        output = Path(job.output_path).with_suffix(".seedance_dry_run.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("Seedance dry run placeholder. No request was sent.\n", encoding="utf-8")
        return VideoClip(
            clip_id=f"seedance_dry_run_{job.scene_id}",
            scene_id=job.scene_id,
            path=str(output),
            duration_seconds=job.duration_seconds,
            provider=self.provider_name,
        )

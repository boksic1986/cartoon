from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import SeedanceDryRunJob, VideoClip, VideoGenerationJob
from idiom_video.utils.json_io import write_json


class SeedanceVideoProvider:
    provider_name = "seedance"

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def generate(self, job: VideoGenerationJob) -> VideoClip:
        if not self.dry_run:
            raise NotImplementedError("Real Seedance API integration is deferred to a later milestone.")
        intended_output = Path(job.output_path)
        output = intended_output.with_suffix(".seedance_dry_run.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        dry_run_job = SeedanceDryRunJob(
            dry_run_id=f"seedance_{job.job_id}",
            source_job_id=job.job_id,
            scene_id=job.scene_id,
            image_path=Path(job.image_path).as_posix(),
            prompt=job.prompt,
            duration_seconds=job.duration_seconds,
            intended_output_path=intended_output.as_posix(),
            request_preview_path=output.as_posix(),
        )
        write_json(output, dry_run_job)
        return VideoClip(
            clip_id=f"seedance_dry_run_{job.scene_id}",
            scene_id=job.scene_id,
            path=output.as_posix(),
            duration_seconds=job.duration_seconds,
            provider=self.provider_name,
        )

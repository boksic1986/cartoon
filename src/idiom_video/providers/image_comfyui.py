from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import ComfyUIDryRunJob, ImageAsset, ImageGenerationJob
from idiom_video.utils.json_io import write_json


class ComfyUIImageProvider:
    provider_name = "comfyui"

    def __init__(self, workflow_path: str | Path | None = None, dry_run: bool = True) -> None:
        self.workflow_path = Path(workflow_path) if workflow_path else None
        self.dry_run = dry_run

    def generate(self, job: ImageGenerationJob) -> ImageAsset:
        if self.workflow_path is None or not self.workflow_path.exists():
            raise FileNotFoundError(f"ComfyUI workflow not found: {self.workflow_path}")
        if not self.dry_run:
            raise NotImplementedError("Real ComfyUI API integration is deferred to a later milestone.")
        intended_output = Path(job.output_path)
        output = intended_output.with_suffix(".comfyui_dry_run.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        dry_run_job = ComfyUIDryRunJob(
            dry_run_id=f"comfyui_{job.job_id}",
            source_job_id=job.job_id,
            scene_id=job.scene_id,
            workflow_path=self.workflow_path.as_posix(),
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            seed=job.seed,
            width=job.width,
            height=job.height,
            intended_output_path=intended_output.as_posix(),
            request_preview_path=output.as_posix(),
        )
        write_json(output, dry_run_job)
        asset = ImageAsset(
            asset_id=f"dry_run_{job.scene_id}",
            scene_id=job.scene_id,
            path=output.as_posix(),
            metadata_path=output.as_posix(),
            provider=self.provider_name,
            seed=job.seed,
            width=job.width,
            height=job.height,
        )
        return asset

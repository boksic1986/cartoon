from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import ImageAsset, ImageGenerationJob


class ComfyUIImageProvider:
    provider_name = "comfyui"

    def __init__(self, workflow_path: str | Path | None = None, dry_run: bool = True) -> None:
        self.workflow_path = Path(workflow_path) if workflow_path else None
        self.dry_run = dry_run

    def generate(self, job: ImageGenerationJob) -> ImageAsset:
        if not self.dry_run:
            raise NotImplementedError("Real ComfyUI API integration is deferred to a later milestone.")
        output = Path(job.output_path).with_suffix(".comfyui_dry_run.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "ComfyUI dry run placeholder. No request was sent.\n",
            encoding="utf-8",
        )
        return ImageAsset(
            asset_id=f"dry_run_{job.scene_id}",
            scene_id=job.scene_id,
            path=str(output),
            metadata_path=str(output),
            provider=self.provider_name,
            seed=job.seed,
            width=job.width,
            height=job.height,
        )

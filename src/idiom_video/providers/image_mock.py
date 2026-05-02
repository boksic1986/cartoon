from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from idiom_video.schemas import ImageAsset, ImageGenerationJob
from idiom_video.utils.json_io import write_json


class ImageMockProvider:
    provider_name = "mock"

    def generate(self, job: ImageGenerationJob) -> ImageAsset:
        output = Path(job.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        image = Image.new("RGB", (job.width, job.height), color=(244, 222, 181))
        draw = ImageDraw.Draw(image)
        draw.rectangle((24, 24, job.width - 24, job.height - 24), outline=(92, 124, 88), width=8)
        draw.text((48, 48), f"MOCK {job.scene_id}", fill=(64, 64, 64))
        draw.text((48, 96), f"seed={job.seed}", fill=(64, 64, 64))
        image.save(output)

        metadata_path = output.with_suffix(".metadata.json")
        asset = ImageAsset(
            asset_id=f"asset_{job.scene_id}",
            scene_id=job.scene_id,
            path=str(output),
            metadata_path=str(metadata_path),
            provider=self.provider_name,
            seed=job.seed,
            width=job.width,
            height=job.height,
        )
        write_json(
            metadata_path,
            {
                "job": job,
                "asset": asset,
                "note": "Mock image generated locally. No external service was called.",
            },
        )
        return asset

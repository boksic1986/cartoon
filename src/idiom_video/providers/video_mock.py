from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import VideoClip, VideoGenerationJob


class VideoMockProvider:
    provider_name = "mock"

    def generate(self, job: VideoGenerationJob) -> VideoClip:
        output = Path(job.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(
                [
                    f"mock video clip: {job.scene_id}",
                    f"image: {job.image_path}",
                    f"duration_seconds: {job.duration_seconds}",
                    f"prompt: {job.prompt}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return VideoClip(
            clip_id=f"clip_{job.scene_id}",
            scene_id=job.scene_id,
            path=str(output),
            duration_seconds=job.duration_seconds,
            provider=self.provider_name,
        )

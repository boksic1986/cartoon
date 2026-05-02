from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import VoiceAsset, VoiceJob
from idiom_video.utils.json_io import write_json


class TTSMockProvider:
    provider_name = "mock"

    def synthesize(self, job: VoiceJob) -> VoiceAsset:
        output = Path(job.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        duration = job.end_seconds - job.start_seconds
        output.write_text(
            "\n".join(
                [
                    "Mock TTS asset only.",
                    f"job_id={job.job_id}",
                    f"cue_id={job.cue_id}",
                    f"scene_id={job.scene_id}",
                    f"speaker={job.speaker_name}",
                    f"duration_seconds={duration:.3f}",
                    f"text={job.text}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        metadata_path = output.with_suffix(".metadata.json")
        asset = VoiceAsset(
            asset_id=f"audio_{job.cue_id}",
            cue_id=job.cue_id,
            scene_id=job.scene_id,
            path=output.as_posix(),
            metadata_path=metadata_path.as_posix(),
            duration_seconds=duration,
            provider=self.provider_name,
        )
        write_json(metadata_path, asset)
        return asset

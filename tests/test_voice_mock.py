from pathlib import Path

from idiom_video.providers.tts_mock import TTSMockProvider
from idiom_video.schemas import VoiceJob


def test_tts_mock_provider_writes_auditable_text_asset(tmp_path):
    job = VoiceJob(
        job_id="voice_scene_01_narration",
        cue_id="scene_01_narration",
        scene_id="scene_01",
        speaker_id="narrator",
        speaker_name="旁白",
        text="很久以前，有个农夫叫阿木。",
        emotion="warm",
        start_seconds=0,
        end_seconds=3,
        output_path=(tmp_path / "audio" / "scene_01_narration.txt").as_posix(),
    )

    asset = TTSMockProvider().synthesize(job)

    assert Path(asset.path).exists()
    assert asset.cue_id == job.cue_id
    assert asset.duration_seconds == 3
    assert "很久以前" in Path(asset.path).read_text(encoding="utf-8")

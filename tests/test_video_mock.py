from pathlib import Path

from idiom_video.providers.video_mock import VideoMockProvider
from idiom_video.schemas import VideoGenerationJob


def test_video_mock_provider_writes_clip_record(tmp_path):
    output = tmp_path / "videos" / "scene_01.txt"
    job = VideoGenerationJob(
        job_id="video_scene_01",
        scene_id="scene_01",
        image_path=str(tmp_path / "images_approved" / "scene_01.png"),
        prompt="gentle movement",
        duration_seconds=5.0,
        output_path=str(output),
    )

    clip = VideoMockProvider().generate(job)

    assert Path(clip.path).exists()
    assert "gentle movement" in Path(clip.path).read_text(encoding="utf-8")


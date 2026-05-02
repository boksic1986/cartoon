from pathlib import Path

import pytest

from idiom_video.providers.video_seedance import SeedanceVideoProvider
from idiom_video.schemas import SeedanceDryRunJob, VideoGenerationJob
from idiom_video.utils.json_io import read_json


def _video_job(tmp_path: Path) -> VideoGenerationJob:
    return VideoGenerationJob(
        job_id="video_scene_01",
        scene_id="scene_01",
        image_path=(tmp_path / "images_approved" / "scene_01.png").as_posix(),
        prompt="温和推镜，农田中人物轻微抬头，儿童教育动画。",
        duration_seconds=5,
        output_path=(tmp_path / "videos" / "scene_01.txt").as_posix(),
        provider="seedance",
    )


def test_seedance_provider_writes_structured_dry_run_job(tmp_path):
    job = _video_job(tmp_path)
    provider = SeedanceVideoProvider(dry_run=True)

    clip = provider.generate(job)

    assert clip.provider == "seedance"
    assert clip.path.endswith(".seedance_dry_run.json")
    payload = read_json(clip.path)
    dry_run_job = SeedanceDryRunJob.model_validate(payload)
    assert dry_run_job.dry_run is True
    assert dry_run_job.source_job_id == "video_scene_01"
    assert dry_run_job.intended_output_path.endswith("videos/scene_01.txt")
    assert dry_run_job.request_preview_path == clip.path


def test_seedance_provider_refuses_real_generation_until_later_phase(tmp_path):
    provider = SeedanceVideoProvider(dry_run=False)

    with pytest.raises(NotImplementedError, match="deferred"):
        provider.generate(_video_job(tmp_path))

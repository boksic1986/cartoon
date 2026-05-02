from pathlib import Path

import pytest

from idiom_video.schemas import Storyboard
from idiom_video.utils.json_io import read_json
from idiom_video.voice_builder import build_alignment, build_lipsync_jobs, build_voice_jobs


FIXTURES = Path(__file__).parent / "fixtures"


def test_build_voice_jobs_creates_one_job_per_speech_cue(tmp_path):
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))

    jobs = build_voice_jobs(storyboard, tmp_path)

    assert len(jobs) == 1
    assert jobs[0].cue_id == "scene_01_narration"
    assert jobs[0].speaker_name == "旁白"
    assert jobs[0].output_path.endswith("audio/scene_01_narration.txt")


def test_build_alignment_and_lipsync_jobs_stay_mock_first(tmp_path):
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    voice_jobs = build_voice_jobs(storyboard, tmp_path)

    alignment = build_alignment(storyboard, voice_jobs)
    lipsync_jobs = build_lipsync_jobs(alignment, tmp_path)

    assert alignment[0].cue_id == "scene_01_narration"
    assert alignment[0].tokens[0].text == storyboard.scenes[0].speech_cues[0].voice_text
    assert lipsync_jobs[0].enabled is False
    assert "MVP" in lipsync_jobs[0].reason


def test_build_alignment_requires_one_voice_job_per_speech_cue(tmp_path):
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))

    with pytest.raises(ValueError, match="missing voice job"):
        build_alignment(storyboard, [])


def test_build_alignment_rejects_duplicate_voice_jobs(tmp_path):
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    voice_jobs = build_voice_jobs(storyboard, tmp_path)

    with pytest.raises(ValueError, match="duplicate voice job"):
        build_alignment(storyboard, [voice_jobs[0], voice_jobs[0]])

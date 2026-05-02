from pathlib import Path

from idiom_video.schemas import IdiomProfile
from idiom_video.script_writer import build_script
from idiom_video.storyboard_writer import build_storyboard
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_storyboard_has_scene_timing_and_speech_cues():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    script = build_script(profile)
    storyboard = build_storyboard(script)

    assert storyboard.idiom_slug == "shou-zhu-dai-tu"
    assert 4 <= len(storyboard.scenes) <= 10
    assert sum(scene.duration_seconds for scene in storyboard.scenes) <= 60
    assert any(cue.kind == "dialogue" for scene in storyboard.scenes for cue in scene.speech_cues)
    assert all(cue.lip_sync_required is False for scene in storyboard.scenes for cue in scene.speech_cues)


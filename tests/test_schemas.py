from pathlib import Path

import pytest
from pydantic import ValidationError

from idiom_video.schemas import IdiomProfile, Storyboard, StoryboardScene
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_idiom_profile_loads_fixture():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))

    assert profile.slug == "shou-zhu-dai-tu"
    assert profile.characters[0].id == "farmer_amu"


def test_idiom_profile_requires_characters():
    data = read_json(FIXTURES / "idiom_sample.json")
    data["characters"] = []

    with pytest.raises(ValidationError):
        IdiomProfile.model_validate(data)


def test_storyboard_rejects_more_than_sixty_seconds():
    scene = StoryboardScene(
        scene_id="scene_01",
        order=1,
        title="Too long",
        visual_description="A long scene",
        camera="static",
        action="wait",
        duration_seconds=61,
        image_prompt_hint="field",
        video_prompt_hint="slow movement",
        speech_cues=[],
    )

    with pytest.raises(ValidationError):
        Storyboard(idiom_slug="x", title="x", scenes=[scene])


def test_speech_cue_keeps_lip_sync_disabled_by_default():
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    cue = storyboard.scenes[0].speech_cues[0]

    assert cue.lip_sync_required is False
    assert cue.mouth_action == "none"


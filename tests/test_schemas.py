from pathlib import Path

import pytest
from pydantic import ValidationError

from idiom_video.schemas import AlignmentCue, IdiomProfile, LipSyncJob, Storyboard, StoryboardScene, VoiceJob
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


def test_voice_alignment_and_lipsync_schemas_are_strict():
    voice_job = VoiceJob(
        job_id="voice_scene_01_narration",
        cue_id="scene_01_narration",
        scene_id="scene_01",
        speaker_id="narrator",
        speaker_name="旁白",
        text="很久以前，有个农夫叫阿木。",
        emotion="warm",
        start_seconds=0,
        end_seconds=3,
        output_path="outputs/story/audio/scene_01_narration.txt",
    )
    alignment = AlignmentCue(
        cue_id=voice_job.cue_id,
        scene_id=voice_job.scene_id,
        speaker_id=voice_job.speaker_id,
        text=voice_job.text,
        audio_path=voice_job.output_path,
        start_seconds=voice_job.start_seconds,
        end_seconds=voice_job.end_seconds,
        tokens=[],
    )
    lipsync_job = LipSyncJob(
        job_id="lipsync_scene_01_narration",
        cue_id=voice_job.cue_id,
        scene_id=voice_job.scene_id,
        audio_path=voice_job.output_path,
        alignment_path="outputs/story/07_alignment.json",
        enabled=False,
        reason="MVP 旁白不需要精确口型同步",
        output_path="outputs/story/lipsync/scene_01_narration.txt",
    )

    assert voice_job.provider == "mock"
    assert alignment.duration_seconds == 3
    assert lipsync_job.enabled is False

    payload = voice_job.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        VoiceJob.model_validate(payload)

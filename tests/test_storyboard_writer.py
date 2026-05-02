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


def test_storyboard_carries_ten_frame_comedy_actions():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    script = build_script(profile)

    storyboard = build_storyboard(script)

    assert len(storyboard.scenes) == 10
    scene_by_id = {scene.scene_id: scene for scene in storyboard.scenes}
    assert "小板凳" in scene_by_id["scene_06"].action
    assert "落叶" in scene_by_id["scene_07"].action
    assert "重新锄地" in scene_by_id["scene_10"].action
    assert storyboard.scenes[-1].speech_cues[-1].estimated_end_seconds <= 60


def test_storyboard_directs_rabbit_motion_and_safe_dizzy_impact():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    storyboard = build_storyboard(build_script(profile))
    scene_by_id = {scene.scene_id: scene for scene in storyboard.scenes}

    assert "朝树桩方向" in scene_by_id["scene_02"].action
    assert "跑向树桩" in scene_by_id["scene_02"].image_prompt_hint
    assert "躺在地上" in scene_by_id["scene_03"].action
    assert "头晕小星星" in scene_by_id["scene_03"].action
    assert "无血迹" in scene_by_id["scene_03"].action


def test_storyboard_waiting_beats_have_distinct_actions_and_crop_progression():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    storyboard = build_storyboard(build_script(profile))
    scene_by_id = {scene.scene_id: scene for scene in storyboard.scenes}

    assert "小板凳" in scene_by_id["scene_06"].action
    assert "空手托腮" in scene_by_id["scene_06"].action
    assert "锄" not in scene_by_id["scene_06"].action
    assert "趴在草席上" in scene_by_id["scene_07"].action
    assert "小虫" in scene_by_id["scene_07"].action
    assert "锄" not in scene_by_id["scene_07"].action
    assert "打盹" in scene_by_id["scene_08"].action
    assert "锄" not in scene_by_id["scene_08"].action
    assert "坐起身" in scene_by_id["scene_09"].action
    assert "锄" not in scene_by_id["scene_09"].action
    assert "春末" in scene_by_id["scene_06"].action
    assert "树叶浓绿" in scene_by_id["scene_06"].action
    assert "初夏" in scene_by_id["scene_07"].action
    assert "远山青绿" in scene_by_id["scene_07"].action
    assert "夏末" in scene_by_id["scene_08"].action
    assert "叶尖发黄" in scene_by_id["scene_08"].action
    assert "树冠开始泛黄" in scene_by_id["scene_08"].action
    assert "初秋" in scene_by_id["scene_09"].action
    assert "更多杂草" in scene_by_id["scene_09"].action
    assert "远山偏灰蓝" in scene_by_id["scene_09"].action


def test_waiting_image_hints_include_seasonal_background_changes():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    storyboard = build_storyboard(build_script(profile))
    scene_by_id = {scene.scene_id: scene for scene in storyboard.scenes}

    assert "树叶浓绿" in scene_by_id["scene_06"].image_prompt_hint
    assert "远山青绿" in scene_by_id["scene_07"].image_prompt_hint
    assert "树冠开始泛黄" in scene_by_id["scene_08"].image_prompt_hint
    assert "远山偏灰蓝" in scene_by_id["scene_09"].image_prompt_hint


def test_storyboard_prompts_keep_house_and_field_path_consistent():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    storyboard = build_storyboard(build_script(profile))

    for scene in storyboard.scenes:
        assert "同一座茅草屋始终位于画面右后方" in scene.image_prompt_hint
        assert "田间小径始终从画面右下角弯向右后方茅草屋" in scene.image_prompt_hint
        assert "经过树桩右侧" in scene.image_prompt_hint


def test_storyboard_prompt_hints_do_not_duplicate_punctuation():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))
    storyboard = build_storyboard(build_script(profile))

    assert all("。。" not in scene.image_prompt_hint for scene in storyboard.scenes)

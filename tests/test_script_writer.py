from pathlib import Path

from idiom_video.schemas import IdiomProfile
from idiom_video.script_writer import build_script
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_shou_zhu_dai_tu_script_expands_to_ten_light_comedy_beats():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))

    script = build_script(profile)

    assert len(script.scenes) == 10
    assert [scene.order for scene in script.scenes] == list(range(1, 11))
    assert sum(scene.duration_seconds for scene in script.scenes) <= 60
    assert [scene.title for scene in script.scenes] == [
        "清晨耕田",
        "小兔跑来",
        "树桩惊喜",
        "好运误会",
        "幻想排队",
        "搬凳等待",
        "落叶虚惊",
        "田地荒了",
        "阿木醒悟",
        "重新耕田",
    ]


def test_shou_zhu_dai_tu_script_uses_gentle_comedy_without_changing_moral():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))

    script = build_script(profile)
    all_text = "\n".join(cue.voice_text for scene in script.scenes for cue in scene.speech_cues)

    assert "好运气是不是认识路" in all_text
    assert "晕乎乎地躺在树桩旁" in all_text
    assert "兔子不会每天打卡" in all_text
    assert "勤劳和思考" in all_text
    assert "血" not in all_text
    assert all(cue.lip_sync_required is False for scene in script.scenes for cue in scene.speech_cues)

from pathlib import Path

from idiom_video.media.subtitle import format_srt_time, storyboard_to_srt
from idiom_video.schemas import Storyboard
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_format_srt_time():
    assert format_srt_time(65.25) == "00:01:05,250"


def test_storyboard_to_srt_contains_cue_text():
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    text = storyboard_to_srt(storyboard)

    assert "1\n00:00:00,000 --> 00:00:05,000" in text
    assert "很久以前" in text

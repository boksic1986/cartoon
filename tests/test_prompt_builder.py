from pathlib import Path

from idiom_video.prompt_builder import build_image_jobs, build_image_prompts
from idiom_video.schemas import Storyboard
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_build_image_prompts_merges_style_and_negative_prompt():
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    prompts = build_image_prompts(
        storyboard,
        style_text="原创中国风儿童绘本动画，温暖明亮。",
        negative_text="不要出现品牌 logo、明星脸、复杂文字。",
    )

    assert prompts[0].scene_id == "scene_01"
    assert "原创中国风儿童绘本动画" in prompts[0].prompt
    assert "品牌 logo" in prompts[0].negative_prompt


def test_build_image_jobs_uses_provider_neutral_filename(tmp_path):
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    prompts = build_image_prompts(storyboard, "style", "negative")
    jobs = build_image_jobs(prompts, tmp_path)

    assert jobs[0].job_id == "image_scene_01"
    assert jobs[0].output_path.endswith("images_raw/scene_01.png")

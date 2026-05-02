from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_run_all_writes_auto_review_records(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    result = CliRunner().invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert result.exit_code == 0, result.output

    review_dir = tmp_path / "outputs" / "shou-zhu-dai-tu" / "review"
    script_review = read_json(review_dir / "script_review.json")
    image_review = read_json(review_dir / "image_review.json")
    video_review = read_json(review_dir / "video_review.json")

    assert script_review["review_type"] == "script"
    assert script_review["summary"]["approved"] == 1
    assert image_review["summary"]["approved"] == 6
    assert image_review["items"][0]["status"] == "approved"
    assert video_review["summary"]["approved"] == 6


def test_approve_images_writes_image_review_with_scene_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    for command in [
        ["generate-script", str(FIXTURES / "idiom_sample.json")],
        ["generate-storyboard", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "01_script.json")],
        ["build-image-prompts", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json")],
        ["generate-images", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"), "--provider", "mock"],
        ["approve-images", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "images_raw"), "--auto"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    review = read_json(tmp_path / "outputs" / "shou-zhu-dai-tu" / "review" / "image_review.json")
    assert review["auto"] is True
    assert review["items"][0]["scene_id"] == "scene_01"
    assert review["items"][0]["asset_path"].endswith("images_approved/scene_01.png")


def test_approve_images_marks_missing_scene_image_pending(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    for command in [
        ["generate-script", str(FIXTURES / "idiom_sample.json")],
        ["generate-storyboard", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "01_script.json")],
        ["build-image-prompts", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json")],
        ["generate-images", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"), "--provider", "mock"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    (story_dir / "images_raw" / "scene_01.png").unlink()

    result = runner.invoke(app, ["approve-images", str(story_dir / "images_raw"), "--auto"])

    assert result.exit_code == 0, result.output
    review = read_json(story_dir / "review" / "image_review.json")
    first = next(item for item in review["items"] if item["scene_id"] == "scene_01")
    jobs = read_json(story_dir / "05_video_jobs.json")
    assert first["status"] == "pending"
    assert first["asset_path"] is None
    assert review["summary"]["approved"] == 5
    assert review["summary"]["pending"] == 1
    assert len(jobs) == 5

from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_quality_check_writes_full_report_for_mock_run(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output

    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["ok"] is True
    assert report["checks"]["required_files"] == "passed"
    assert report["checks"]["approved_images"] == "passed"
    assert report["checks"]["review_records"] == "passed"


def test_quality_check_fails_when_approved_image_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    (story_dir / "images_approved" / "scene_01.png").unlink()

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["ok"] is False
    assert any("approved image missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_review_item_is_pending(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    review_path = story_dir / "review" / "image_review.json"
    review = read_json(review_path)
    review["items"][0]["status"] = "pending"
    review["items"][0]["notes"] = "等待人工复核。"
    write_json(review_path, review)

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["ok"] is False
    assert any("review item is pending" in issue["message"] for issue in report["issues"])

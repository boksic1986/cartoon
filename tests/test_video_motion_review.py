from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import VideoMotionReview
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_seedance_dry_run_story(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    for command in [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_build_video_motion_review_writes_auto_approved_review(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])

    assert result.exit_code == 0, result.output
    review = VideoMotionReview.model_validate(read_json(story_dir / "review" / "video_motion_review.json"))
    storyboard = read_json(story_dir / "02_storyboard.json")
    assert len(review.items) == len(storyboard["scenes"])
    assert review.auto is True
    assert review.summary["pending"] == 0
    assert all(item.status == "approved" for item in review.items)
    assert all(item.continuity_prompt_present for item in review.items)
    assert all(Path(item.image_path).exists() for item in review.items)
    assert all(Path(item.request_preview_path).exists() for item in review.items)


def test_build_video_motion_review_defaults_to_pending_without_auto(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir)])

    assert result.exit_code == 0, result.output
    review = VideoMotionReview.model_validate(read_json(story_dir / "review" / "video_motion_review.json"))
    assert review.auto is False
    assert review.summary["pending"] == len(review.items)
    assert all(item.status == "pending" for item in review.items)


def test_quality_check_validates_video_motion_review_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])
    assert build.exit_code == 0, build.output
    packet = CliRunner().invoke(app, ["build-review-packet", str(story_dir)])
    assert packet.exit_code == 0, packet.output

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["video_motion_review_schema"] == "passed"
    assert report["checks"]["video_motion_review_files"] == "passed"


def test_quality_check_fails_when_video_motion_review_is_pending(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir)])
    assert build.exit_code == 0, build.output

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["video_motion_review_files"] == "failed"
    assert any("video motion review item is pending" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_video_motion_review_file_reference_is_missing(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])
    assert build.exit_code == 0, build.output
    review_path = story_dir / "review" / "video_motion_review.json"
    review = read_json(review_path)
    Path(review["items"][0]["request_preview_path"]).unlink()
    write_json(review_path, review)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["video_motion_review_files"] == "failed"
    assert any("video motion review request preview missing" in issue["message"] for issue in report["issues"])


def test_quality_check_reports_invalid_video_motion_review_schema_without_crashing(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])
    assert build.exit_code == 0, build.output
    packet = CliRunner().invoke(app, ["build-review-packet", str(story_dir)])
    assert packet.exit_code == 0, packet.output
    review_path = story_dir / "review" / "video_motion_review.json"
    review = read_json(review_path)
    review["unexpected"] = "reject"
    write_json(review_path, review)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    assert result.exception.__class__.__name__ == "SystemExit"
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["video_motion_review_schema"] == "failed"


def test_quality_check_fails_when_video_motion_review_contains_stale_scene(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])
    assert build.exit_code == 0, build.output
    review_path = story_dir / "review" / "video_motion_review.json"
    review = read_json(review_path)
    stale_item = dict(review["items"][0])
    stale_item["item_id"] = "motion_old_scene"
    stale_item["scene_id"] = "old_scene"
    stale_item["title"] = "旧镜头 运动审核"
    review["items"].append(stale_item)
    review["summary"]["approved"] += 1
    write_json(review_path, review)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["video_motion_review_files"] == "failed"
    assert any("video motion review scene is not in current Seedance dry-run jobs" in issue["message"] for issue in report["issues"])


def test_build_review_packet_includes_video_motion_review_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_seedance_dry_run_story(tmp_path, monkeypatch)
    build = CliRunner().invoke(app, ["build-video-motion-review", str(story_dir), "--auto"])
    assert build.exit_code == 0, build.output

    result = CliRunner().invoke(app, ["build-review-packet", str(story_dir)])

    assert result.exit_code == 0, result.output
    packet = read_json(story_dir / "review" / "review_packet.json")
    video_items = [item for item in packet["items"] if item["item_type"] == "video"]
    assert video_items
    for item in video_items:
        assert (story_dir / "review" / "video_motion_review.json").as_posix() in item["artifact_paths"]

from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.media.review_video import build_review_video_plan
from idiom_video.schemas import ReviewVideoManifest, ReviewVideoPlan
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_review_story(tmp_path: Path) -> Path:
    story_dir = tmp_path / "story"
    write_json(story_dir / "02_storyboard.json", read_json(FIXTURES / "storyboard_sample.json"))
    approved_dir = story_dir / "images_approved"
    approved_dir.mkdir(parents=True)
    Image.new("RGB", (320, 480), color=(226, 198, 140)).save(approved_dir / "scene_01.png")
    return story_dir


def test_build_review_video_plan_references_approved_images(tmp_path):
    story_dir = _prepare_review_story(tmp_path)

    plan = build_review_video_plan(story_dir, width=360, height=640, fps=6)

    assert plan.idiom_slug == "shou-zhu-dai-tu"
    assert plan.width == 360
    assert plan.height == 640
    assert plan.fps == 6
    assert plan.output_path.endswith("final/review_v1.mp4")
    assert plan.fallback_path.endswith("final/review_v1.gif")
    assert len(plan.clips) == 1
    assert plan.clips[0].scene_id == "scene_01"
    assert plan.clips[0].image_path.endswith("images_approved/scene_01.png")
    assert plan.clips[0].start_seconds == 0
    assert plan.clips[0].end_seconds == 5
    assert plan.clips[0].subtitle_text


def test_compose_review_video_force_fallback_writes_review_artifacts(tmp_path):
    story_dir = _prepare_review_story(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "compose-review-video",
            str(story_dir),
            "--force-fallback",
            "--width",
            "360",
            "--height",
            "640",
            "--fps",
            "4",
        ],
    )

    assert result.exit_code == 0, result.output
    plan = ReviewVideoPlan.model_validate(read_json(story_dir / "09_review_video_plan.json"))
    manifest = ReviewVideoManifest.model_validate(read_json(story_dir / "final" / "review_v1_manifest.json"))
    assert len(plan.clips) == 1
    assert manifest.ok is True
    assert manifest.used_ffmpeg is False
    assert manifest.provider == "pillow_gif_fallback"
    assert manifest.output_path.endswith("final/review_v1.gif")
    assert manifest.fallback_note_path is not None
    assert Path(manifest.output_path).exists()
    assert Path(manifest.fallback_note_path).exists()


def _prepare_full_review_video_story(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    for command in [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        [
            "compose-review-video",
            str(story_dir),
            "--force-fallback",
            "--width",
            "180",
            "--height",
            "320",
            "--fps",
            "4",
        ],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_quality_check_fails_when_review_video_manifest_is_not_ok(tmp_path, monkeypatch):
    story_dir = _prepare_full_review_video_story(tmp_path, monkeypatch)
    manifest_path = story_dir / "final" / "review_v1_manifest.json"
    manifest = read_json(manifest_path)
    manifest["ok"] = False
    write_json(manifest_path, manifest)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_video_manifest_files"] == "failed"
    assert any("review video manifest is not ok" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_review_video_manifest_drifts_from_plan(tmp_path, monkeypatch):
    story_dir = _prepare_full_review_video_story(tmp_path, monkeypatch)
    manifest_path = story_dir / "final" / "review_v1_manifest.json"
    manifest = read_json(manifest_path)
    manifest["provider"] = "local_ffmpeg"
    manifest["clip_count"] += 1
    write_json(manifest_path, manifest)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_video_manifest_files"] == "failed"
    assert any("provider does not match used_ffmpeg" in issue["message"] for issue in report["issues"])
    assert any("clip count differs from review video plan" in issue["message"] for issue in report["issues"])

from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import ReviewPacket
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_build_review_packet_writes_editable_packet(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"

    result = runner.invoke(app, ["build-review-packet", str(story_dir)])

    assert result.exit_code == 0, result.output
    packet = ReviewPacket.model_validate(read_json(story_dir / "review" / "review_packet.json"))
    assert packet.idiom_slug == "shou-zhu-dai-tu"
    assert packet.summary["pending"] == 0
    item_types = {item.item_type for item in packet.items}
    assert {"script", "image", "video", "voice", "lipsync"}.issubset(item_types)
    assert all(item.status == "approved" for item in packet.items)
    assert all(item.checklist for item in packet.items)


def test_build_review_packet_includes_comfyui_dry_run_previews_when_present(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    dry_run = runner.invoke(
        app,
        [
            "generate-images",
            str(story_dir / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"),
        ],
    )
    assert dry_run.exit_code == 0, dry_run.output

    result = runner.invoke(app, ["build-review-packet", str(story_dir)])

    assert result.exit_code == 0, result.output
    packet = ReviewPacket.model_validate(read_json(story_dir / "review" / "review_packet.json"))
    image_items = [item for item in packet.items if item.item_type == "image"]
    assert image_items
    for item in image_items:
        assert (story_dir / "comfyui_dry_run" / "jobs.json").as_posix() in item.artifact_paths
        assert any(path.endswith(f"{item.scene_id}.comfyui_dry_run.json") for path in item.artifact_paths)


def test_quality_check_validates_review_packet_when_present(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    build = runner.invoke(app, ["build-review-packet", str(story_dir)])
    assert build.exit_code == 0, build.output

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_packet_schema"] == "passed"
    assert report["checks"]["review_packet_files"] == "passed"


def test_quality_check_fails_when_review_packet_artifact_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    build = runner.invoke(app, ["build-review-packet", str(story_dir)])
    assert build.exit_code == 0, build.output
    packet = read_json(story_dir / "review" / "review_packet.json")
    first_image = next(item for item in packet["items"] if item["item_type"] == "image")
    Path(first_image["artifact_paths"][0]).unlink()

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_packet_files"] == "failed"
    assert any("review packet artifact missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_comfyui_dry_run_is_newer_than_review_packet(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    build = runner.invoke(app, ["build-review-packet", str(story_dir)])
    assert build.exit_code == 0, build.output
    dry_run = runner.invoke(
        app,
        [
            "generate-images",
            str(story_dir / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"),
        ],
    )
    assert dry_run.exit_code == 0, dry_run.output

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_packet_files"] == "failed"
    assert any("ComfyUI dry-run request preview missing from review packet" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_dry_run_is_newer_than_review_packet(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    build = runner.invoke(app, ["build-review-packet", str(story_dir)])
    assert build.exit_code == 0, build.output
    dry_run = runner.invoke(
        app,
        [
            "generate-videos",
            str(story_dir / "05_video_jobs.json"),
            "--provider",
            "seedance",
            "--dry-run",
        ],
    )
    assert dry_run.exit_code == 0, dry_run.output

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["review_packet_files"] == "failed"
    assert any("Seedance dry-run request preview missing from review packet" in issue["message"] for issue in report["issues"])

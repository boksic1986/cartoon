from pathlib import Path

import pytest
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
    assert report["checks"]["script_schema"] == "passed"
    assert report["checks"]["storyboard_schema"] == "passed"
    assert report["checks"]["image_prompts_schema"] == "passed"
    assert report["checks"]["image_jobs_schema"] == "passed"
    assert report["checks"]["video_jobs_schema"] == "passed"
    assert report["checks"]["voice_jobs_schema"] == "passed"
    assert report["checks"]["alignment_schema"] == "passed"
    assert report["checks"]["lipsync_jobs_schema"] == "passed"
    assert report["checks"]["voice_assets"] == "passed"
    assert report["checks"]["alignment_assets"] == "passed"
    assert report["checks"]["lipsync_outputs"] == "passed"
    assert report["checks"]["metadata_schema"] == "passed"
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


@pytest.mark.parametrize(
    ("artifact", "remove_path", "expected_check"),
    [
        ("01_script.json", ("scenes",), "script_schema"),
        ("02_storyboard.json", ("scenes",), "storyboard_schema"),
        ("03_image_prompts.json", (0, "prompt"), "image_prompts_schema"),
        ("04_image_jobs.json", (0, "output_path"), "image_jobs_schema"),
        ("05_video_jobs.json", (0, "output_path"), "video_jobs_schema"),
        ("06_voice_jobs.json", (0, "output_path"), "voice_jobs_schema"),
        ("07_alignment.json", (0, "audio_path"), "alignment_schema"),
        ("08_lipsync_jobs.json", (0, "output_path"), "lipsync_jobs_schema"),
        ("final/metadata.json", ("title",), "metadata_schema"),
    ],
)
def test_quality_check_fails_invalid_core_artifact_schema(tmp_path, monkeypatch, artifact, remove_path, expected_check):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    artifact_path = story_dir / artifact
    payload = read_json(artifact_path)
    if len(remove_path) == 1:
        payload.pop(remove_path[0])
    else:
        payload[remove_path[0]].pop(remove_path[1])
    write_json(artifact_path, payload)

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["ok"] is False
    assert report["checks"][expected_check] == "failed"
    assert any(
        artifact in issue.get("path", "") and "schema validation failed" in issue["message"]
        for issue in report["issues"]
    )


def test_quality_check_fails_core_artifact_unknown_field(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    script_path = story_dir / "01_script.json"
    script = read_json(script_path)
    script["unexpected_field"] = "schema should reject this"
    write_json(script_path, script)

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["script_schema"] == "failed"
    assert any("unexpected_field" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_voice_asset_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    (story_dir / "audio" / "scene_01_narration.txt").unlink()

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["voice_assets"] == "failed"
    assert any("voice asset missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_alignment_audio_reference_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    alignment_path = story_dir / "07_alignment.json"
    alignment = read_json(alignment_path)
    alignment[0]["audio_path"] = (story_dir / "audio" / "missing.txt").as_posix()
    write_json(alignment_path, alignment)

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["alignment_assets"] == "failed"
    assert any("alignment audio missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_lipsync_output_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    lipsync_jobs = read_json(story_dir / "08_lipsync_jobs.json")
    Path(lipsync_jobs[0]["output_path"]).unlink()

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["lipsync_outputs"] == "failed"
    assert any("lipsync output missing" in issue["message"] for issue in report["issues"])


def test_quality_check_validates_comfyui_dry_run_jobs_when_present(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    commands = [
        [
            "generate-images",
            str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"),
        ],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["comfyui_dry_run_schema"] == "passed"
    assert report["checks"]["comfyui_dry_run_files"] == "passed"


def test_quality_check_fails_when_comfyui_dry_run_preview_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    run = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert run.exit_code == 0, run.output
    dry_run = runner.invoke(
        app,
        [
            "generate-images",
            str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"),
        ],
    )
    assert dry_run.exit_code == 0, dry_run.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    dry_run_jobs = read_json(story_dir / "comfyui_dry_run" / "jobs.json")
    Path(dry_run_jobs[0]["request_preview_path"]).unlink()

    result = runner.invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["comfyui_dry_run_files"] == "failed"
    assert any("dry-run request preview missing" in issue["message"] for issue in report["issues"])

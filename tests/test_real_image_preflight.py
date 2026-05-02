from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import RealImagePreflightReport
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _reviewed_workflow(tmp_path: Path) -> Path:
    workflow_path = tmp_path / "workflows" / "text2image_reviewed.json"
    write_json(
        workflow_path,
        {
            "workflow": "idiom_story_text2image",
            "nodes": [
                {"id": "checkpoint", "class_type": "CheckpointLoaderSimple"},
                {"id": "sampler", "class_type": "KSampler"},
            ],
        },
    )
    return workflow_path


def _reviewed_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "models_manifest.json"
    write_json(
        manifest_path,
        {
            "models": [
                {
                    "name": "idiom_story_sdxl_checkpoint",
                    "type": "checkpoint",
                    "local_path": "D:/ComfyUI/models/checkpoints/idiom_story_sdxl.safetensors",
                    "source": "manual_reviewed",
                    "license": "LICENSE_REVIEWED",
                    "commercial_use_allowed": True,
                    "notes": "测试用已审核记录，不代表真实模型文件。",
                }
            ]
        },
    )
    return manifest_path


def _prepare_story(tmp_path: Path, monkeypatch, workflow_path: Path) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        [
            "generate-images",
            str(story_dir / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(workflow_path),
        ],
        ["build-review-packet", str(story_dir)],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def _prepare_stale_review_story(tmp_path: Path, monkeypatch, workflow_path: Path) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["build-review-packet", str(story_dir)],
        [
            "generate-images",
            str(story_dir / "03_image_prompts.json"),
            "--provider",
            "comfyui",
            "--dry-run",
            "--workflow",
            str(workflow_path),
        ],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_real_image_preflight_passes_and_stops_before_generation(tmp_path, monkeypatch):
    workflow_path = _reviewed_workflow(tmp_path)
    manifest_path = _reviewed_manifest(tmp_path)
    story_dir = _prepare_story(tmp_path, monkeypatch, workflow_path)

    result = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )

    assert result.exit_code == 0, result.output
    report = RealImagePreflightReport.model_validate(read_json(story_dir / "quality_reports" / "real_image_preflight.json"))
    assert report.ok is True
    assert report.next_step == "STOP_BEFORE_REAL_IMAGE_GENERATION"
    assert Path(report.smoke_report_path).exists()
    assert report.checks["comfyui_smoke"] == "passed"
    assert report.checks["review_packet"] == "passed"
    assert "generate real images" in report.stop_reason


def test_real_image_preflight_fails_for_placeholder_workflow_and_manifest(tmp_path, monkeypatch):
    workflow_path = Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"
    manifest_path = Path("data") / "models" / "models_manifest.json"
    story_dir = _prepare_story(tmp_path, monkeypatch, workflow_path)

    result = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "real_image_preflight.json")
    assert report["ok"] is False
    assert Path(report["smoke_report_path"]).exists()
    assert report["checks"]["comfyui_smoke"] == "failed"
    assert any("ComfyUI smoke check must pass" in issue["message"] for issue in report["issues"])


def test_real_image_preflight_fails_when_review_packet_misses_comfyui_dry_run_previews(tmp_path, monkeypatch):
    workflow_path = _reviewed_workflow(tmp_path)
    manifest_path = _reviewed_manifest(tmp_path)
    story_dir = _prepare_stale_review_story(tmp_path, monkeypatch, workflow_path)

    result = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "real_image_preflight.json")
    assert report["checks"]["review_packet"] == "failed"
    assert any("ComfyUI dry-run request preview missing from review packet" in issue["message"] for issue in report["issues"])


def test_quality_check_validates_successful_real_image_preflight_when_present(tmp_path, monkeypatch):
    workflow_path = _reviewed_workflow(tmp_path)
    manifest_path = _reviewed_manifest(tmp_path)
    story_dir = _prepare_story(tmp_path, monkeypatch, workflow_path)
    preflight = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )
    assert preflight.exit_code == 0, preflight.output

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_image_preflight_schema"] == "passed"
    assert report["checks"]["real_image_preflight"] == "passed"
    assert report["checks"]["real_image_preflight_consistency"] == "passed"


def test_quality_check_reruns_real_image_preflight_when_inputs_change(tmp_path, monkeypatch):
    workflow_path = _reviewed_workflow(tmp_path)
    manifest_path = _reviewed_manifest(tmp_path)
    story_dir = _prepare_story(tmp_path, monkeypatch, workflow_path)
    preflight = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )
    assert preflight.exit_code == 0, preflight.output
    write_json(workflow_path, {"workflow": "placeholder_after_review"})

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_image_preflight_consistency"] == "failed"
    assert any("current real image preflight no longer passes" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_preflight_smoke_report_is_missing(tmp_path, monkeypatch):
    workflow_path = _reviewed_workflow(tmp_path)
    manifest_path = _reviewed_manifest(tmp_path)
    story_dir = _prepare_story(tmp_path, monkeypatch, workflow_path)
    preflight = CliRunner().invoke(
        app,
        [
            "real-image-preflight",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )
    assert preflight.exit_code == 0, preflight.output
    report = RealImagePreflightReport.model_validate(read_json(story_dir / "quality_reports" / "real_image_preflight.json"))
    Path(report.smoke_report_path).unlink()

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    full_report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert full_report["checks"]["real_image_preflight_smoke_report"] == "failed"
    assert any("preflight smoke report missing" in issue["message"] for issue in full_report["issues"])

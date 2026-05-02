from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_dry_run_story(tmp_path: Path, monkeypatch, workflow_path: Path) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        [
            "generate-images",
            str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"),
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
    return tmp_path / "outputs" / "shou-zhu-dai-tu"


def test_comfyui_smoke_check_passes_reviewed_workflow_manifest_and_matching_dry_run(tmp_path, monkeypatch):
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
                    "notes": "测试用已审核占位记录，不代表真实模型文件。",
                }
            ]
        },
    )
    story_dir = _prepare_dry_run_story(tmp_path, monkeypatch, workflow_path)

    result = CliRunner().invoke(
        app,
        [
            "comfyui-smoke-check",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(manifest_path),
        ],
    )

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "comfyui_smoke_check.json")
    assert report["ok"] is True
    assert report["checks"]["workflow_json"] == "passed"
    assert report["checks"]["models_manifest_readiness"] == "passed"
    assert report["checks"]["dry_run_workflow_match"] == "passed"


def test_comfyui_smoke_check_fails_when_placeholder_artifacts_remain(tmp_path, monkeypatch):
    workflow_path = Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"
    story_dir = _prepare_dry_run_story(tmp_path, monkeypatch, workflow_path)

    result = CliRunner().invoke(
        app,
        [
            "comfyui-smoke-check",
            str(story_dir),
            "--workflow",
            str(workflow_path),
            "--manifest",
            str(Path("data") / "models" / "models_manifest.json"),
        ],
    )

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "comfyui_smoke_check.json")
    assert report["ok"] is False
    messages = [issue["message"] for issue in report["issues"]]
    assert any("placeholder" in message for message in messages)

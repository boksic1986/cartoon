from pathlib import Path

import pytest

from idiom_video.providers.image_comfyui import ComfyUIImageProvider
from idiom_video.schemas import ImageGenerationJob
from idiom_video.utils.json_io import read_json


def _image_job(tmp_path: Path) -> ImageGenerationJob:
    return ImageGenerationJob(
        job_id="image_scene_01",
        scene_id="scene_01",
        prompt="原创中国风儿童绘本动画，古代农田",
        negative_prompt="no logo",
        output_path=(tmp_path / "images_raw" / "scene_01.png").as_posix(),
        seed=123,
        width=768,
        height=1344,
        provider="comfyui",
    )


def test_comfyui_provider_writes_structured_dry_run_job(tmp_path):
    workflow_path = tmp_path / "workflow.placeholder.json"
    workflow_path.write_text('{"kind": "placeholder"}\n', encoding="utf-8")
    provider = ComfyUIImageProvider(workflow_path=workflow_path, dry_run=True)

    asset = provider.generate(_image_job(tmp_path))

    assert asset.provider == "comfyui"
    assert asset.path.endswith(".comfyui_dry_run.json")
    payload = read_json(asset.path)
    assert payload["dry_run"] is True
    assert payload["source_job_id"] == "image_scene_01"
    assert payload["workflow_path"] == workflow_path.as_posix()
    assert payload["intended_output_path"].endswith("images_raw/scene_01.png")


def test_comfyui_provider_requires_workflow_path_for_dry_run(tmp_path):
    provider = ComfyUIImageProvider(workflow_path=tmp_path / "missing.json", dry_run=True)

    with pytest.raises(FileNotFoundError, match="ComfyUI workflow not found"):
        provider.generate(_image_job(tmp_path))


def test_comfyui_provider_refuses_real_generation_until_later_phase(tmp_path):
    workflow_path = tmp_path / "workflow.placeholder.json"
    workflow_path.write_text('{"kind": "placeholder"}\n', encoding="utf-8")
    provider = ComfyUIImageProvider(workflow_path=workflow_path, dry_run=False)

    with pytest.raises(NotImplementedError, match="deferred"):
        provider.generate(_image_job(tmp_path))

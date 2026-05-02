from pathlib import Path

from PIL import Image

from idiom_video.providers.image_mock import ImageMockProvider
from idiom_video.schemas import ImageGenerationJob


def test_image_mock_provider_writes_png_and_metadata(tmp_path):
    output = tmp_path / "images_raw" / "scene_01.png"
    job = ImageGenerationJob(
        job_id="image_scene_01",
        scene_id="scene_01",
        prompt="warm field",
        negative_prompt="no logo",
        output_path=str(output),
        seed=123,
        width=320,
        height=568,
    )

    asset = ImageMockProvider().generate(job)

    assert Path(asset.path).exists()
    assert Path(asset.metadata_path).exists()
    with Image.open(asset.path) as image:
        assert image.size == (320, 568)


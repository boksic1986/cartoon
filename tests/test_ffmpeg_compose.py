from pathlib import Path

from idiom_video.media.ffmpeg_compose import compose_mock_final


def test_compose_writes_fallback_when_ffmpeg_missing(tmp_path):
    project_dir = tmp_path / "story"
    result = compose_mock_final(project_dir, ffmpeg_path="definitely-not-existing-ffmpeg")

    assert result.used_ffmpeg is False
    assert Path(result.output_path).name == "final_mock.txt"
    assert Path(result.output_path).exists()


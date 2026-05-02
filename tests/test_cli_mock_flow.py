from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app


FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_run_all_mock_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()

    result = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])

    assert result.exit_code == 0, result.output
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    assert (story_dir / "01_script.json").exists()
    assert (story_dir / "02_storyboard.json").exists()
    assert (story_dir / "03_image_prompts.json").exists()
    assert (story_dir / "04_image_jobs.json").exists()
    assert (story_dir / "05_video_jobs.json").exists()
    assert (story_dir / "subtitles" / "final.srt").exists()
    assert (story_dir / "final" / "metadata.json").exists()
    assert (story_dir / "final" / "final_mock.txt").exists() or (story_dir / "final" / "final_mock.mp4").exists()


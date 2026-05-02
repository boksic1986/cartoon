from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.utils.json_io import read_json, write_json


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
    assert (story_dir / "06_voice_jobs.json").exists()
    assert (story_dir / "audio" / "voice_assets.json").exists()
    assert (story_dir / "07_alignment.json").exists()
    assert (story_dir / "08_lipsync_jobs.json").exists()
    assert (story_dir / "subtitles" / "final.srt").exists()
    assert (story_dir / "final" / "metadata.json").exists()
    assert (story_dir / "final" / "final_mock.txt").exists() or (story_dir / "final" / "final_mock.mp4").exists()


def test_cli_single_step_flow_writes_quality_report(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()

    commands = [
        ["validate-idiom", str(FIXTURES / "idiom_sample.json")],
        ["generate-script", str(FIXTURES / "idiom_sample.json")],
        ["generate-storyboard", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "01_script.json")],
        ["build-image-prompts", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json")],
        ["generate-images", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "03_image_prompts.json"), "--provider", "mock"],
        ["approve-images", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "images_raw"), "--auto"],
        ["generate-videos", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "05_video_jobs.json"), "--provider", "mock"],
        ["build-voice-jobs", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json")],
        ["generate-audio", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "06_voice_jobs.json"), "--provider", "mock"],
        ["build-lipsync-jobs", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "07_alignment.json")],
        ["generate-subtitles", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json")],
        ["compose", str(tmp_path / "outputs" / "shou-zhu-dai-tu")],
        ["publish-metadata", str(tmp_path / "outputs" / "shou-zhu-dai-tu")],
    ]

    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    report = read_json(tmp_path / "outputs" / "shou-zhu-dai-tu" / "quality_reports" / "prompt_quality.json")
    assert report["ok"] is True
    assert report["issues"] == []


def test_build_image_prompts_blocks_forbidden_positive_prompt(tmp_path):
    story_dir = tmp_path / "story"
    story_dir.mkdir()
    storyboard = read_json(FIXTURES / "storyboard_sample.json")
    storyboard["scenes"][0]["visual_description"] = "请生成明星脸角色站在古代农田里。"
    storyboard_path = story_dir / "02_storyboard.json"
    write_json(storyboard_path, storyboard)

    result = CliRunner().invoke(app, ["build-image-prompts", str(storyboard_path)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "prompt_quality.json")
    assert report["ok"] is False
    assert report["issues"][0]["term"] == "明星脸"


def test_build_image_prompts_allows_forbidden_terms_in_negative_prompt(tmp_path):
    story_dir = tmp_path / "story"
    story_dir.mkdir()
    storyboard_path = story_dir / "02_storyboard.json"
    write_json(storyboard_path, read_json(FIXTURES / "storyboard_sample.json"))

    result = CliRunner().invoke(app, ["build-image-prompts", str(storyboard_path)])

    assert result.exit_code == 0, result.output
    prompts = read_json(story_dir / "03_image_prompts.json")
    report = read_json(story_dir / "quality_reports" / "prompt_quality.json")
    assert "明星脸" in prompts[0]["negative_prompt"]
    assert report["ok"] is True


def test_generate_images_comfyui_dry_run_writes_reviewable_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    storyboard_path = tmp_path / "outputs" / "shou-zhu-dai-tu" / "02_storyboard.json"
    workflow_path = Path("workflows") / "comfyui" / "text2image_sdxl.placeholder.json"
    commands = [
        ["generate-script", str(FIXTURES / "idiom_sample.json")],
        ["generate-storyboard", str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "01_script.json")],
        ["build-image-prompts", str(storyboard_path)],
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

    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    assets = read_json(story_dir / "images_raw" / "assets.json")
    dry_run_jobs = read_json(story_dir / "comfyui_dry_run" / "jobs.json")
    assert assets[0]["provider"] == "comfyui"
    assert dry_run_jobs[0]["dry_run"] is True
    assert Path(assets[0]["path"]).exists()


def test_generate_videos_seedance_dry_run_writes_reviewable_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        [
            "generate-videos",
            str(tmp_path / "outputs" / "shou-zhu-dai-tu" / "05_video_jobs.json"),
            "--provider",
            "seedance",
            "--dry-run",
        ],
    ]

    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    clips = read_json(story_dir / "videos" / "clips.json")
    dry_run_jobs = read_json(story_dir / "seedance_dry_run" / "jobs.json")
    assert clips[0]["provider"] == "seedance"
    assert dry_run_jobs[0]["dry_run"] is True
    assert Path(clips[0]["path"]).exists()

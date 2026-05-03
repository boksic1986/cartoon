from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import SeedanceCostEstimate
from idiom_video.seedance_cost import estimate_seedance_cost, video_jobs_fingerprint
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_story_with_video_jobs(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    result = runner.invoke(app, ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"])
    assert result.exit_code == 0, result.output
    return story_dir


def test_estimate_seedance_cost_from_video_jobs(tmp_path, monkeypatch):
    story_dir = _prepare_story_with_video_jobs(tmp_path, monkeypatch)

    estimate = estimate_seedance_cost(
        story_dir,
        model_name="Dreamina-Seedance-2.0",
        width=864,
        height=496,
        fps=24,
        currency="USD",
        unit_price_per_million_tokens=7,
        retry_multiplier=1.2,
        billing_mode="input_without_video",
        price_source="manual test price",
        price_source_url="https://docs.byteplus.com/docs/ModelArk/1099320",
        price_checked_at="2026-05-03",
    )

    assert estimate.provider == "seedance"
    assert estimate.clip_count == 10
    assert estimate.total_duration_seconds == 51
    assert estimate.estimated_tokens == 512244
    assert estimate.base_cost == 3.5857
    assert estimate.estimated_total_cost == 4.3028
    assert estimate.video_jobs_path.endswith("05_video_jobs.json")
    assert estimate.video_jobs_fingerprint.startswith("sha256:")
    assert estimate.price_source_url == "https://docs.byteplus.com/docs/ModelArk/1099320"
    assert estimate.price_checked_at == "2026-05-03"


def test_estimate_video_cost_cli_writes_reviewable_json(tmp_path, monkeypatch):
    story_dir = _prepare_story_with_video_jobs(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        app,
        [
            "estimate-video-cost",
            str(story_dir),
            "--model-name",
            "Dreamina-Seedance-2.0",
            "--width",
            "864",
            "--height",
            "496",
            "--fps",
            "24",
            "--currency",
            "USD",
            "--unit-price-per-million-tokens",
            "7",
            "--retry-multiplier",
            "1.2",
            "--billing-mode",
            "input_without_video",
            "--price-source",
            "BytePlus official ModelArk pricing page checked manually",
            "--price-source-url",
            "https://docs.byteplus.com/docs/ModelArk/1099320",
            "--price-checked-at",
            "2026-05-03",
        ],
    )

    assert result.exit_code == 0, result.output
    estimate = SeedanceCostEstimate.model_validate(
        read_json(story_dir / "quality_reports" / "seedance_cost_estimate.json")
    )
    assert estimate.estimated_total_cost == 4.3028
    assert estimate.price_source == "BytePlus official ModelArk pricing page checked manually"
    assert estimate.price_source_url == "https://docs.byteplus.com/docs/ModelArk/1099320"
    assert estimate.price_checked_at == "2026-05-03"


def test_quality_check_validates_seedance_cost_estimate_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_story_with_video_jobs(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        [
            "estimate-video-cost",
            str(story_dir),
            "--unit-price-per-million-tokens",
            "7",
            "--currency",
            "USD",
        ],
    )
    assert result.exit_code == 0, result.output

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code == 0, quality.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_cost_estimate_schema"] == "passed"
    assert report["checks"]["seedance_cost_estimate_consistency"] == "passed"


def test_quality_check_fails_when_seedance_cost_estimate_is_stale(tmp_path, monkeypatch):
    story_dir = _prepare_story_with_video_jobs(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        [
            "estimate-video-cost",
            str(story_dir),
            "--unit-price-per-million-tokens",
            "7",
            "--currency",
            "USD",
        ],
    )
    assert result.exit_code == 0, result.output
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    video_jobs[0]["duration_seconds"] = 6
    write_json(video_jobs_path, video_jobs)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_cost_estimate_consistency"] == "failed"
    assert any("Seedance cost estimate is stale" in issue["message"] for issue in report["issues"])


def test_video_jobs_fingerprint_is_not_path_style_dependent(tmp_path, monkeypatch):
    story_dir = _prepare_story_with_video_jobs(tmp_path, monkeypatch)
    video_jobs_path = story_dir / "05_video_jobs.json"
    relative_path = video_jobs_path.relative_to(tmp_path)

    monkeypatch.chdir(tmp_path)

    assert video_jobs_fingerprint(relative_path) == video_jobs_fingerprint(video_jobs_path)

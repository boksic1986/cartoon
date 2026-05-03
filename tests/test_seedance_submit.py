from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import SeedanceSubmitPlan
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_submit_ready_story(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
        ["estimate-video-cost", str(story_dir), "--unit-price-per-million-tokens", "7", "--currency", "USD"],
        ["build-video-motion-review", str(story_dir), "--auto"],
        ["build-review-packet", str(story_dir)],
        ["real-video-preflight", str(story_dir)],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_prepare_seedance_submit_writes_plan_without_secret(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)
    monkeypatch.setenv("SEEDANCE_API_KEY", "secret-key-that-must-not-leak")

    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    )

    assert result.exit_code == 0, result.output
    plan_path = story_dir / "seedance_submit" / "submit_plan.json"
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "secret-key-that-must-not-leak" not in plan_text
    assert "Authorization" not in plan_text
    plan = SeedanceSubmitPlan.model_validate(read_json(plan_path))
    assert plan.ok is True
    assert plan.item_count == 10
    assert plan.estimated_total_cost == 4.3028
    assert plan.max_cost == 5
    assert plan.next_step == "STOP_BEFORE_REAL_SEEDANCE_SUBMIT"


def test_prepare_seedance_submit_requires_external_call_confirmation(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(app, ["prepare-seedance-submit", str(story_dir), "--max-cost", "5"])

    assert result.exit_code != 0
    assert not (story_dir / "seedance_submit" / "submit_plan.json").exists()
    assert "--confirm-external-call" in result.output


def test_prepare_seedance_submit_blocks_when_budget_is_too_low(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "1", "--confirm-external-call"],
    )

    assert result.exit_code != 0
    assert "exceeds max cost" in result.output


def test_prepare_seedance_submit_rejects_non_finite_budget(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "nan", "--confirm-external-call"],
    )

    assert result.exit_code != 0
    assert "finite positive number" in result.output
    assert not (story_dir / "seedance_submit" / "submit_plan.json").exists()


def test_prepare_seedance_submit_refuses_execute_real_flag(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        app,
        [
            "prepare-seedance-submit",
            str(story_dir),
            "--max-cost",
            "5",
            "--confirm-external-call",
            "--execute-real",
        ],
    )

    assert result.exit_code != 0
    assert not (story_dir / "seedance_submit" / "submit_plan.json").exists()
    assert "real Seedance submission is not implemented" in result.output


def test_quality_check_validates_seedance_submit_plan_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    )
    assert result.exit_code == 0, result.output

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code == 0, quality.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_submit_plan_schema"] == "passed"
    assert report["checks"]["seedance_submit_plan_consistency"] == "passed"


def test_quality_check_fails_when_seedance_submit_plan_is_stale(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    )
    assert result.exit_code == 0, result.output
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    video_jobs[0]["prompt"] = "changed after submit plan"
    write_json(video_jobs_path, video_jobs)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_submit_plan_consistency"] == "failed"
    assert any("Seedance submit plan is stale" in issue["message"] for issue in report["issues"])


def test_quality_check_rejects_unsafe_seedance_submit_plan_flags(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    )
    assert result.exit_code == 0, result.output
    plan_path = story_dir / "seedance_submit" / "submit_plan.json"
    plan = read_json(plan_path)
    plan["dry_run"] = False
    plan["execute_real_requested"] = True
    plan["provider"] = "seedance-prod"
    write_json(plan_path, plan)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_submit_plan_schema"] == "failed"


def test_prepare_seedance_submit_blocks_sensitive_strings_in_upstream_artifacts(tmp_path, monkeypatch):
    story_dir = _prepare_submit_ready_story(tmp_path, monkeypatch)
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    video_jobs[0]["prompt"] = f"{video_jobs[0]['prompt']} Authorization: Bearer sk-secret"
    write_json(video_jobs_path, video_jobs)
    runner = CliRunner()
    for command in [
        ["generate-videos", str(video_jobs_path), "--provider", "seedance", "--dry-run"],
        ["estimate-video-cost", str(story_dir), "--unit-price-per-million-tokens", "7", "--currency", "USD"],
        ["build-video-motion-review", str(story_dir), "--auto"],
        ["build-review-packet", str(story_dir)],
        ["real-video-preflight", str(story_dir)],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    result = CliRunner().invoke(
        app,
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    )

    assert result.exit_code != 0
    assert "sensitive string" in result.output
    assert not (story_dir / "seedance_submit" / "submit_plan.json").exists()

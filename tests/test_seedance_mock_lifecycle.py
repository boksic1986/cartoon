from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import SeedanceTaskBatch, SeedanceTaskResults
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_submit_plan(tmp_path: Path, monkeypatch) -> Path:
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
        ["prepare-seedance-submit", str(story_dir), "--max-cost", "5", "--confirm-external-call"],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_submit_seedance_tasks_mock_writes_reviewable_artifacts_without_secret(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("SEEDANCE_API_KEY", "secret-key-that-must-not-leak")

    result = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "mock"])

    assert result.exit_code == 0, result.output
    batch_path = story_dir / "seedance_tasks" / "submissions.json"
    batch_text = batch_path.read_text(encoding="utf-8")
    assert "secret-key-that-must-not-leak" not in batch_text
    assert "Authorization" not in batch_text
    batch = SeedanceTaskBatch.model_validate(read_json(batch_path))
    assert batch.ok is True
    assert batch.dry_run is True
    assert batch.client == "mock"
    assert batch.task_count == 10
    assert batch.next_step == "MOCK_POLL_SEEDANCE_TASKS"
    assert Path(batch.tasks[0].submit_request_path).exists()
    assert Path(batch.tasks[0].submit_response_path).exists()


def test_submit_seedance_tasks_refuses_real_provider(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)

    result = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "seedance"])

    assert result.exit_code != 0
    assert "real Seedance task submission is not implemented" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_submit_seedance_tasks_blocks_sensitive_submit_plan_values(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    plan_path = story_dir / "seedance_submit" / "submit_plan.json"
    plan = read_json(plan_path)
    plan["items"][0]["prompt"] = f"{plan['items'][0]['prompt']} Authorization: Bearer sk-secret"
    write_json(plan_path, plan)

    result = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "mock"])

    assert result.exit_code != 0
    assert "sensitive string" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_poll_seedance_tasks_mock_writes_results_and_placeholder_clips(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    submit = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "mock"])
    assert submit.exit_code == 0, submit.output

    result = CliRunner().invoke(app, ["poll-seedance-tasks", str(story_dir), "--provider", "mock"])

    assert result.exit_code == 0, result.output
    results = SeedanceTaskResults.model_validate(read_json(story_dir / "seedance_tasks" / "results.json"))
    assert results.ok is True
    assert results.task_count == 10
    assert all(item.status == "succeeded" for item in results.results)
    assert Path(results.results[0].output_path).exists()
    clips = read_json(story_dir / "videos" / "seedance_clips.json")
    assert len(clips) == 10
    assert clips[0]["provider"] == "seedance_mock"


def test_poll_seedance_tasks_refuses_real_provider(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    submit = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "mock"])
    assert submit.exit_code == 0, submit.output

    result = CliRunner().invoke(app, ["poll-seedance-tasks", str(story_dir), "--provider", "seedance"])

    assert result.exit_code != 0
    assert "real Seedance task polling is not implemented" in result.output


def test_quality_check_validates_seedance_task_lifecycle_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    for command in [
        ["submit-seedance-tasks", str(story_dir), "--provider", "mock"],
        ["poll-seedance-tasks", str(story_dir), "--provider", "mock"],
    ]:
        result = CliRunner().invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code == 0, quality.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_submissions_schema"] == "passed"
    assert report["checks"]["seedance_task_submissions_files"] == "passed"
    assert report["checks"]["seedance_task_results_schema"] == "passed"
    assert report["checks"]["seedance_task_results_files"] == "passed"


def test_quality_check_fails_when_seedance_task_output_is_missing(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    for command in [
        ["submit-seedance-tasks", str(story_dir), "--provider", "mock"],
        ["poll-seedance-tasks", str(story_dir), "--provider", "mock"],
    ]:
        result = CliRunner().invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    results = read_json(story_dir / "seedance_tasks" / "results.json")
    Path(results["results"][0]["output_path"]).unlink()

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("Seedance mock output missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_task_result_misses_submission(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    for command in [
        ["submit-seedance-tasks", str(story_dir), "--provider", "mock"],
        ["poll-seedance-tasks", str(story_dir), "--provider", "mock"],
    ]:
        result = CliRunner().invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    submissions_path = story_dir / "seedance_tasks" / "submissions.json"
    submissions = read_json(submissions_path)
    submissions["tasks"] = submissions["tasks"][1:]
    submissions["task_count"] -= 1
    write_json(submissions_path, submissions)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("Seedance task results differ from submissions" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_clips_manifest_is_missing(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    for command in [
        ["submit-seedance-tasks", str(story_dir), "--provider", "mock"],
        ["poll-seedance-tasks", str(story_dir), "--provider", "mock"],
    ]:
        result = CliRunner().invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    (story_dir / "videos" / "seedance_clips.json").unlink()

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("Seedance clips manifest missing" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_task_artifact_contains_sensitive_string(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    for command in [
        ["submit-seedance-tasks", str(story_dir), "--provider", "mock"],
        ["poll-seedance-tasks", str(story_dir), "--provider", "mock"],
    ]:
        result = CliRunner().invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    request_path = story_dir / "seedance_tasks" / "scene_01.submit_request.json"
    request_payload = read_json(request_path)
    request_payload["debug"] = "Authorization: Bearer sk-secret"
    write_json(request_path, request_payload)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_submissions_files"] == "failed"
    assert any("sensitive string" in issue["message"] for issue in report["issues"])

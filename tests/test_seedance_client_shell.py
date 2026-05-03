from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import (
    SeedanceClientDownloadRequest,
    SeedanceClientDownloadResponse,
    SeedanceClientPollRequest,
    SeedanceClientPollResponse,
    SeedanceClientSubmitRequest,
    SeedanceClientSubmitResponse,
    SeedanceTaskBatch,
    SeedanceTaskResults,
)
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


def test_seedance_client_contract_schemas_are_strict():
    submit_request = SeedanceClientSubmitRequest(
        source_job_id="video_scene_01",
        scene_id="scene_01",
        image_path="outputs/story/images/scene_01.png",
        prompt="中国风卡通田间镜头",
        duration_seconds=5,
        intended_output_path="outputs/story/videos/scene_01.mp4",
    )
    submit_response = SeedanceClientSubmitResponse(
        task_id="seedance_mock_http_scene_01",
        scene_id="scene_01",
        status="submitted",
        retry_after_seconds=2,
    )
    poll_request = SeedanceClientPollRequest(task_id=submit_response.task_id, scene_id="scene_01")
    poll_response = SeedanceClientPollResponse(
        task_id=submit_response.task_id,
        scene_id="scene_01",
        status="succeeded",
        progress_percent=100,
    )
    download_request = SeedanceClientDownloadRequest(task_id=submit_response.task_id, scene_id="scene_01")
    download_response = SeedanceClientDownloadResponse(
        task_id=submit_response.task_id,
        scene_id="scene_01",
        status="downloaded",
        output_path="outputs/story/videos/scene_01.seedance_mock_http.txt",
    )

    assert submit_request.client == "mock_http"
    assert submit_request.dry_run is True
    assert submit_response.client == "mock_http"
    assert poll_request.client == "mock_http"
    assert poll_response.progress_percent == 100
    assert download_request.client == "mock_http"
    assert download_response.output_path.endswith(".seedance_mock_http.txt")


def test_submit_seedance_tasks_seedance_dry_run_uses_mock_http_contract(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("SEEDANCE_API_KEY", "secret-key-that-must-not-leak")

    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )

    assert result.exit_code == 0, result.output
    batch_path = story_dir / "seedance_tasks" / "submissions.json"
    batch_text = batch_path.read_text(encoding="utf-8")
    assert "secret-key-that-must-not-leak" not in batch_text
    assert "Authorization" not in batch_text
    batch = SeedanceTaskBatch.model_validate(read_json(batch_path))
    assert batch.client == "mock_http"
    assert batch.dry_run is True
    assert batch.task_count == 10
    first_task = batch.tasks[0]
    assert first_task.task_id.startswith("seedance_mock_http_")
    assert Path(first_task.submit_request_path).exists()
    assert Path(first_task.submit_response_path).exists()
    submit_request = SeedanceClientSubmitRequest.model_validate(read_json(first_task.submit_request_path))
    submit_response = SeedanceClientSubmitResponse.model_validate(read_json(first_task.submit_response_path))
    assert submit_request.scene_id == first_task.scene_id
    assert submit_response.task_id == first_task.task_id


def test_submit_seedance_tasks_seedance_provider_requires_dry_run_and_confirmation(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)

    real_result = CliRunner().invoke(
        app,
        ["submit-seedance-tasks", str(story_dir), "--provider", "seedance", "--confirm-external-call"],
    )
    unconfirmed_result = CliRunner().invoke(
        app,
        ["submit-seedance-tasks", str(story_dir), "--provider", "seedance", "--dry-run"],
    )

    assert real_result.exit_code != 0
    assert "dry-run" in real_result.output
    assert unconfirmed_result.exit_code != 0
    assert "--confirm-external-call" in unconfirmed_result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_poll_seedance_tasks_seedance_dry_run_writes_contract_results_and_passes_quality(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    runner = CliRunner()
    submit = runner.invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )
    assert submit.exit_code == 0, submit.output

    result = runner.invoke(
        app,
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )

    assert result.exit_code == 0, result.output
    results = SeedanceTaskResults.model_validate(read_json(story_dir / "seedance_tasks" / "results.json"))
    assert results.client == "mock_http"
    assert results.task_count == 10
    first_result = results.results[0]
    assert first_result.provider == "seedance_mock_http"
    assert first_result.poll_request_path is not None
    assert first_result.download_request_path is not None
    assert Path(first_result.output_path).exists()
    SeedanceClientPollRequest.model_validate(read_json(first_result.poll_request_path))
    SeedanceClientPollResponse.model_validate(read_json(first_result.poll_response_path))
    SeedanceClientDownloadRequest.model_validate(read_json(first_result.download_request_path))
    SeedanceClientDownloadResponse.model_validate(read_json(first_result.download_response_path))
    clips = read_json(story_dir / "videos" / "seedance_clips.json")
    assert clips[0]["provider"] == "seedance_mock_http"

    quality = runner.invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code == 0, quality.output


def test_poll_seedance_tasks_seedance_provider_requires_dry_run_and_confirmation(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    submit = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )
    assert submit.exit_code == 0, submit.output

    real_result = CliRunner().invoke(
        app,
        ["poll-seedance-tasks", str(story_dir), "--provider", "seedance", "--confirm-external-call"],
    )
    unconfirmed_result = CliRunner().invoke(
        app,
        ["poll-seedance-tasks", str(story_dir), "--provider", "seedance", "--dry-run"],
    )

    assert real_result.exit_code != 0
    assert "dry-run" in real_result.output
    assert unconfirmed_result.exit_code != 0
    assert "--confirm-external-call" in unconfirmed_result.output


def test_poll_seedance_tasks_refuses_mixed_mock_http_submission_with_mock_provider(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    submit = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )
    assert submit.exit_code == 0, submit.output

    result = CliRunner().invoke(app, ["poll-seedance-tasks", str(story_dir), "--provider", "mock"])

    assert result.exit_code != 0
    assert "requires mock submissions" in result.output


def test_poll_seedance_tasks_refuses_mixed_mock_submission_with_seedance_provider(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    submit = CliRunner().invoke(app, ["submit-seedance-tasks", str(story_dir), "--provider", "mock"])
    assert submit.exit_code == 0, submit.output

    result = CliRunner().invoke(
        app,
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    )

    assert result.exit_code != 0
    assert "requires mock HTTP submissions" in result.output


def test_quality_check_fails_when_seedance_mock_http_request_contains_sensitive_string(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    runner = CliRunner()
    for command in [
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    results = read_json(story_dir / "seedance_tasks" / "results.json")
    poll_request_path = Path(results["results"][0]["poll_request_path"])
    poll_request = read_json(poll_request_path)
    poll_request["debug"] = "Authorization: Bearer sk-secret"
    write_json(poll_request_path, poll_request)

    quality = runner.invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("sensitive string" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_submission_and_result_clients_differ(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    runner = CliRunner()
    for command in [
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    results_path = story_dir / "seedance_tasks" / "results.json"
    results = read_json(results_path)
    results["client"] = "mock"
    write_json(results_path, results)

    quality = runner.invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("Seedance task result client differs from submissions" in issue["message"] for issue in report["issues"])


def test_quality_check_fails_when_seedance_mock_http_response_schema_is_invalid(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    runner = CliRunner()
    for command in [
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--dry-run",
            "--confirm-external-call",
        ],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    results = read_json(story_dir / "seedance_tasks" / "results.json")
    poll_response_path = Path(results["results"][0]["poll_response_path"])
    poll_response = read_json(poll_response_path)
    poll_response["progress_percent"] = 101
    write_json(poll_response_path, poll_response)

    quality = runner.invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_results_files"] == "failed"
    assert any("Seedance mock HTTP artifact schema validation failed" in issue["message"] for issue in report["issues"])

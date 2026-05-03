import json
from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.providers.seedance_client import RealSeedanceHttpTransport, SeedanceApiClient
from idiom_video.schemas import (
    SeedanceClientSubmitRequest,
    SeedanceClientSubmitResponse,
    SeedanceTaskBatch,
    SeedanceTaskResults,
)
from idiom_video.utils.json_io import read_json
from idiom_video.utils.json_io import write_json


FIXTURES = Path(__file__).parent / "fixtures"


class _FakeHttpResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


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


def test_real_seedance_transport_builds_official_shape_without_leaking_key():
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeHttpResponse({"id": "task_real_001", "status": "submitted"})

    transport = RealSeedanceHttpTransport(
        api_key="secret-key-that-must-not-leak",
        base_url="https://ark.example.test/api/v3",
        model_name="seedance-1-0-pro-250528",
        ratio="9:16",
        resolution="720p",
        urlopen=fake_urlopen,
    )
    client = SeedanceApiClient(transport)

    response = client.submit(
        SeedanceClientSubmitRequest(
            client="seedance_real",
            dry_run=False,
            source_job_id="video_scene_01",
            scene_id="scene_01",
            image_path="outputs/story/images/scene_01.png",
            image_url="https://cdn.example.test/scene_01.png",
            prompt="中国风卡通田间镜头",
            duration_seconds=5,
            intended_output_path="outputs/story/videos/scene_01.mp4",
        )
    )

    assert response == SeedanceClientSubmitResponse(
        client="seedance_real",
        dry_run=False,
        task_id="task_real_001",
        scene_id="scene_01",
        status="submitted",
        retry_after_seconds=5,
    )
    assert captured["url"] == "https://ark.example.test/api/v3/contents/generations/tasks"
    assert captured["headers"]["Authorization"] == "Bearer secret-key-that-must-not-leak"
    assert captured["payload"]["model"] == "seedance-1-0-pro-250528"
    assert captured["payload"]["ratio"] == "9:16"
    assert captured["payload"]["resolution"] == "720p"
    assert {"type": "text", "text": "中国风卡通田间镜头"} in captured["payload"]["content"]
    assert {
        "type": "image_url",
        "image_url": {"url": "https://cdn.example.test/scene_01.png"},
        "role": "first_frame",
    } in captured["payload"]["content"]
    assert "secret-key-that-must-not-leak" not in json.dumps(captured["payload"])


def test_submit_seedance_tasks_execute_real_requires_api_key(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    monkeypatch.delenv("SEEDANCE_API_KEY", raising=False)

    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
            "--allow-text-only",
        ],
    )

    assert result.exit_code != 0
    assert "ARK_API_KEY" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_submit_seedance_tasks_execute_real_requires_image_url_unless_text_only(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "secret-key-that-must-not-leak")

    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
        ],
    )

    assert result.exit_code != 0
    assert "public image URL" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_submit_seedance_tasks_execute_real_rejects_non_public_image_urls(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "secret-key-that-must-not-leak")
    image_map_path = story_dir / "seedance_submit" / "image_url_map.json"
    write_json(image_map_path, {"scene_01": "file:///D:/pipeline/cartoon/scene_01.png"})

    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
            "--image-url-map",
            str(image_map_path),
        ],
    )

    assert result.exit_code != 0
    assert "public image URL" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_submit_seedance_tasks_execute_real_rejects_localhost_image_base_url(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "secret-key-that-must-not-leak")

    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
            "--image-base-url",
            "http://127.0.0.1:8000/assets",
        ],
    )

    assert result.exit_code != 0
    assert "public image URL" in result.output
    assert not (story_dir / "seedance_tasks" / "submissions.json").exists()


def test_submit_and_poll_seedance_tasks_execute_real_with_fake_transport(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "secret-key-that-must-not-leak")

    class FakeRealTransport:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def submit(self, request):
            return SeedanceClientSubmitResponse(
                client="seedance_real",
                dry_run=False,
                task_id=f"real_task_{request.scene_id}",
                scene_id=request.scene_id,
                status="submitted",
                retry_after_seconds=1,
            )

        def poll(self, request):
            from idiom_video.schemas import SeedanceClientPollResponse

            return SeedanceClientPollResponse(
                client="seedance_real",
                dry_run=False,
                task_id=request.task_id,
                scene_id=request.scene_id,
                status="succeeded",
                progress_percent=100,
            )

        def download(self, request, *, output_path: str):
            from idiom_video.schemas import SeedanceClientDownloadResponse

            Path(output_path).write_bytes(b"fake mp4 bytes")
            return SeedanceClientDownloadResponse(
                client="seedance_real",
                dry_run=False,
                task_id=request.task_id,
                scene_id=request.scene_id,
                status="downloaded",
                output_path=output_path,
            )

    monkeypatch.setattr("idiom_video.seedance_lifecycle.RealSeedanceHttpTransport", FakeRealTransport)
    runner = CliRunner()
    submit = runner.invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
            "--allow-text-only",
        ],
    )
    assert submit.exit_code == 0, submit.output
    batch_path = story_dir / "seedance_tasks" / "submissions.json"
    batch_text = batch_path.read_text(encoding="utf-8")
    assert "secret-key-that-must-not-leak" not in batch_text
    batch = SeedanceTaskBatch.model_validate(read_json(batch_path))
    assert batch.client == "seedance_real"
    assert batch.dry_run is False
    assert batch.task_count == 1

    poll = runner.invoke(
        app,
        [
            "poll-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--poll-interval-seconds",
            "0",
            "--max-poll-attempts",
            "1",
        ],
    )

    assert poll.exit_code == 0, poll.output
    results = SeedanceTaskResults.model_validate(read_json(story_dir / "seedance_tasks" / "results.json"))
    assert results.client == "seedance_real"
    assert results.dry_run is False
    assert results.task_count == 1
    assert Path(results.results[0].output_path).exists()
    assert results.results[0].provider == "seedance_real"
    quality = runner.invoke(app, ["quality-check", str(story_dir)])
    assert quality.exit_code == 0, quality.output


def test_quality_check_fails_when_real_artifact_client_does_not_match_ledger(tmp_path, monkeypatch):
    story_dir = _prepare_submit_plan(tmp_path, monkeypatch)
    monkeypatch.setenv("ARK_API_KEY", "secret-key-that-must-not-leak")

    class FakeRealTransport:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def submit(self, request):
            return SeedanceClientSubmitResponse(
                client="seedance_real",
                dry_run=False,
                task_id=f"real_task_{request.scene_id}",
                scene_id=request.scene_id,
                status="submitted",
                retry_after_seconds=1,
            )

    monkeypatch.setattr("idiom_video.seedance_lifecycle.RealSeedanceHttpTransport", FakeRealTransport)
    result = CliRunner().invoke(
        app,
        [
            "submit-seedance-tasks",
            str(story_dir),
            "--provider",
            "seedance",
            "--execute-real",
            "--confirm-external-call",
            "--max-real-tasks",
            "1",
            "--allow-text-only",
        ],
    )
    assert result.exit_code == 0, result.output
    submissions = read_json(story_dir / "seedance_tasks" / "submissions.json")
    request_path = Path(submissions["tasks"][0]["submit_request_path"])
    request_payload = read_json(request_path)
    request_payload["client"] = "mock_http"
    request_payload["dry_run"] = True
    write_json(request_path, request_payload)

    quality = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert quality.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["seedance_task_submissions_files"] == "failed"
    assert any("Seedance task artifact client differs from ledger" in issue["message"] for issue in report["issues"])

from pathlib import Path

from typer.testing import CliRunner

from idiom_video.cli import app
from idiom_video.schemas import RealVideoPreflightReport
from idiom_video.utils.json_io import read_json, write_json


FIXTURES = Path(__file__).parent / "fixtures"


def _prepare_video_ready_story(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    commands = [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
        ["estimate-video-cost", str(story_dir), "--unit-price-per-million-tokens", "7", "--currency", "USD"],
        ["build-video-motion-review", str(story_dir), "--auto"],
        ["build-review-packet", str(story_dir)],
    ]
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"
    return story_dir


def test_real_video_preflight_passes_and_stops_before_generation(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)

    result = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = RealVideoPreflightReport.model_validate(
        read_json(story_dir / "quality_reports" / "real_video_preflight.json")
    )
    assert report.ok is True
    assert report.next_step == "STOP_BEFORE_REAL_VIDEO_GENERATION"
    assert report.checks["seedance_dry_run"] == "passed"
    assert report.checks["seedance_cost_estimate"] == "passed"
    assert report.checks["video_motion_review"] == "passed"
    assert report.checks["review_packet"] == "passed"
    assert "generate real videos" in report.stop_reason


def test_real_video_preflight_fails_without_video_motion_review(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    for command in [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
        ["estimate-video-cost", str(story_dir), "--unit-price-per-million-tokens", "7", "--currency", "USD"],
        ["build-review-packet", str(story_dir)],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    result = runner.invoke(app, ["real-video-preflight", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "real_video_preflight.json")
    assert report["ok"] is False
    assert report["checks"]["video_motion_review"] == "failed"
    assert any("video motion review missing" in issue["message"] for issue in report["issues"])


def test_real_video_preflight_fails_when_review_packet_misses_motion_review(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    for command in [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
        ["estimate-video-cost", str(story_dir), "--unit-price-per-million-tokens", "7", "--currency", "USD"],
        ["build-review-packet", str(story_dir)],
        ["build-video-motion-review", str(story_dir), "--auto"],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    result = runner.invoke(app, ["real-video-preflight", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "real_video_preflight.json")
    assert report["checks"]["review_packet"] == "failed"
    assert any("video motion review missing from review packet" in issue["message"] for issue in report["issues"])


def test_real_video_preflight_fails_without_cost_estimate(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "outputs"))
    story_dir = tmp_path / "outputs" / "shou-zhu-dai-tu"
    runner = CliRunner()
    for command in [
        ["run-all", str(FIXTURES / "idiom_sample.json"), "--providers", "mock"],
        ["generate-videos", str(story_dir / "05_video_jobs.json"), "--provider", "seedance", "--dry-run"],
        ["build-video-motion-review", str(story_dir), "--auto"],
        ["build-review-packet", str(story_dir)],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"{command}: {result.output}"

    result = runner.invoke(app, ["real-video-preflight", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "real_video_preflight.json")
    assert report["checks"]["seedance_cost_estimate"] == "failed"
    assert any("Seedance cost estimate missing" in issue["message"] for issue in report["issues"])


def test_quality_check_validates_successful_real_video_preflight_when_present(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code == 0, result.output
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_schema"] == "passed"
    assert report["checks"]["real_video_preflight"] == "passed"
    assert report["checks"]["real_video_preflight_consistency"] == "passed"


def test_quality_check_reruns_real_video_preflight_when_motion_review_changes(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output
    motion_path = story_dir / "review" / "video_motion_review.json"
    motion = read_json(motion_path)
    motion["items"][0]["status"] = "pending"
    motion["summary"]["approved"] -= 1
    motion["summary"]["pending"] += 1
    write_json(motion_path, motion)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_consistency"] == "failed"
    assert any("current real video preflight no longer passes" in issue["message"] for issue in report["issues"])


def test_quality_check_reruns_real_video_preflight_when_video_jobs_change(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    video_jobs[0]["prompt"] = "这个提示词已经在门禁后被改动。"
    write_json(video_jobs_path, video_jobs)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_consistency"] == "failed"
    assert any("Seedance dry-run prompt differs from current video job" in issue["message"] for issue in report["issues"])


def test_quality_check_reruns_real_video_preflight_when_new_video_job_is_added(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    new_job = dict(video_jobs[0])
    new_job["job_id"] = "video_new_scene"
    new_job["scene_id"] = "new_scene"
    new_job["output_path"] = (story_dir / "videos" / "new_scene.txt").as_posix()
    video_jobs.append(new_job)
    write_json(video_jobs_path, video_jobs)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_consistency"] == "failed"
    assert any("current video job missing from Seedance dry-run jobs" in issue["message"] for issue in report["issues"])


def test_quality_check_reruns_real_video_preflight_when_duplicate_scene_video_job_is_added(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs = read_json(video_jobs_path)
    duplicate_scene_job = dict(video_jobs[0])
    duplicate_scene_job["job_id"] = "video_scene_01_alt"
    duplicate_scene_job["output_path"] = (story_dir / "videos" / "scene_01_alt.txt").as_posix()
    video_jobs.insert(0, duplicate_scene_job)
    write_json(video_jobs_path, video_jobs)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_consistency"] == "failed"
    assert any("current video jobs contain duplicate scene_id" in issue["message"] for issue in report["issues"])


def test_quality_check_requires_real_video_preflight_report_to_match_current_artifact_fingerprint(tmp_path, monkeypatch):
    story_dir = _prepare_video_ready_story(tmp_path, monkeypatch)
    preflight = CliRunner().invoke(app, ["real-video-preflight", str(story_dir)])
    assert preflight.exit_code == 0, preflight.output
    report_path = story_dir / "quality_reports" / "real_video_preflight.json"
    saved_report = read_json(report_path)
    current_report = dict(saved_report)
    current_report["artifact_fingerprint"] = "stale-report"
    write_json(report_path, current_report)

    result = CliRunner().invoke(app, ["quality-check", str(story_dir)])

    assert result.exit_code != 0
    report = read_json(story_dir / "quality_reports" / "full_quality.json")
    assert report["checks"]["real_video_preflight_consistency"] == "failed"
    assert any("saved real video preflight report is stale" in issue["message"] for issue in report["issues"])

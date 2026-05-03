from __future__ import annotations

import hashlib
from pathlib import Path

from idiom_video.review_packet import find_review_packet_dry_run_gaps
from idiom_video.schemas import (
    RealVideoPreflightIssue,
    RealVideoPreflightReport,
    ReviewPacket,
    SeedanceDryRunJob,
    VideoGenerationJob,
    VideoMotionReview,
)
from idiom_video.utils.json_io import read_json
from idiom_video.video_motion_review import find_video_motion_review_gaps


FINGERPRINT_PATHS = [
    "02_storyboard.json",
    "05_video_jobs.json",
    "seedance_dry_run/jobs.json",
    "review/video_motion_review.json",
    "review/review_packet.json",
]


def _issue(message: str, path: str | None = None) -> RealVideoPreflightIssue:
    return RealVideoPreflightIssue(message=message, path=path)


def _check_file(path: Path, checks: dict[str, str], issues: list[RealVideoPreflightIssue], check_name: str) -> None:
    if path.exists():
        checks[check_name] = "passed"
        return
    checks[check_name] = "failed"
    issues.append(_issue("required preflight artifact missing", path.as_posix()))


def _check_video_jobs(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealVideoPreflightIssue],
) -> None:
    path = story_dir / "05_video_jobs.json"
    if not path.exists():
        checks["video_jobs"] = "failed"
        issues.append(_issue("video jobs missing", path.as_posix()))
        return
    try:
        jobs = [VideoGenerationJob.model_validate(item) for item in read_json(path)]
    except Exception as exc:
        checks["video_jobs"] = "failed"
        issues.append(_issue(f"video jobs schema validation failed: {exc}", path.as_posix()))
        return
    ok = bool(jobs)
    if not jobs:
        issues.append(_issue("video jobs must not be empty", path.as_posix()))
    seen_scene_ids: set[str] = set()
    seen_job_ids: set[str] = set()
    for job in jobs:
        if job.scene_id in seen_scene_ids:
            ok = False
            issues.append(_issue("current video jobs contain duplicate scene_id", job.scene_id))
        seen_scene_ids.add(job.scene_id)
        if job.job_id in seen_job_ids:
            ok = False
            issues.append(_issue("current video jobs contain duplicate job_id", job.job_id))
        seen_job_ids.add(job.job_id)
    checks["video_jobs"] = "passed" if ok else "failed"


def _check_seedance_dry_run(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealVideoPreflightIssue],
) -> None:
    path = story_dir / "seedance_dry_run" / "jobs.json"
    if not path.exists():
        checks["seedance_dry_run"] = "failed"
        issues.append(_issue("Seedance dry-run jobs missing", path.as_posix()))
        return
    try:
        jobs = [SeedanceDryRunJob.model_validate(item) for item in read_json(path)]
    except Exception as exc:
        checks["seedance_dry_run"] = "failed"
        issues.append(_issue(f"Seedance dry-run schema validation failed: {exc}", path.as_posix()))
        return
    video_jobs_path = story_dir / "05_video_jobs.json"
    video_jobs: list[VideoGenerationJob] = []
    if video_jobs_path.exists():
        try:
            video_jobs = [VideoGenerationJob.model_validate(item) for item in read_json(video_jobs_path)]
        except Exception:
            video_jobs = []
    ok = bool(jobs)
    if not jobs:
        issues.append(_issue("Seedance dry-run jobs must not be empty", path.as_posix()))
    dry_run_by_source_job_id: dict[str, SeedanceDryRunJob] = {}
    dry_run_scene_ids: set[str] = set()
    for job in jobs:
        if job.source_job_id in dry_run_by_source_job_id:
            ok = False
            issues.append(_issue("Seedance dry-run jobs contain duplicate source_job_id", job.source_job_id))
        dry_run_by_source_job_id[job.source_job_id] = job
        if job.scene_id in dry_run_scene_ids:
            ok = False
            issues.append(_issue("Seedance dry-run jobs contain duplicate scene_id", job.scene_id))
        dry_run_scene_ids.add(job.scene_id)
    for source_job in video_jobs:
        if source_job.job_id not in dry_run_by_source_job_id:
            ok = False
            issues.append(_issue("current video job missing from Seedance dry-run jobs", source_job.scene_id))
    for job in jobs:
        source_job = next((video_job for video_job in video_jobs if video_job.job_id == job.source_job_id), None)
        if source_job is None:
            if job.source_job_id not in {video_job.job_id for video_job in video_jobs}:
                ok = False
                issues.append(_issue("Seedance dry-run source job missing from current video jobs", job.source_job_id))
        else:
            if job.scene_id != source_job.scene_id:
                ok = False
                issues.append(_issue("Seedance dry-run scene differs from current video job", job.scene_id))
            if job.source_job_id != source_job.job_id:
                ok = False
                issues.append(_issue("Seedance dry-run source job differs from current video job", job.scene_id))
            if job.image_path != Path(source_job.image_path).as_posix():
                ok = False
                issues.append(_issue("Seedance dry-run image differs from current video job", job.image_path))
            if job.prompt != source_job.prompt:
                ok = False
                issues.append(_issue("Seedance dry-run prompt differs from current video job", job.scene_id))
            if job.duration_seconds != source_job.duration_seconds:
                ok = False
                issues.append(_issue("Seedance dry-run duration differs from current video job", job.scene_id))
            if job.intended_output_path != Path(source_job.output_path).as_posix():
                ok = False
                issues.append(_issue("Seedance dry-run output differs from current video job", job.scene_id))
        if not Path(job.image_path).exists():
            ok = False
            issues.append(_issue("Seedance dry-run image missing", job.image_path))
        if not Path(job.request_preview_path).exists():
            ok = False
            issues.append(_issue("Seedance dry-run request preview missing", job.request_preview_path))
    checks["seedance_dry_run"] = "passed" if ok else "failed"


def _check_video_motion_review(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealVideoPreflightIssue],
) -> None:
    path = story_dir / "review" / "video_motion_review.json"
    if not path.exists():
        checks["video_motion_review"] = "failed"
        issues.append(_issue("video motion review missing", path.as_posix()))
        return
    try:
        review = VideoMotionReview.model_validate(read_json(path))
    except Exception as exc:
        checks["video_motion_review"] = "failed"
        issues.append(_issue(f"video motion review schema validation failed: {exc}", path.as_posix()))
        return
    ok = True
    for item in review.items:
        if item.status != "approved":
            ok = False
            issues.append(_issue(f"video motion review item is {item.status}", f"{path.as_posix()}:{item.item_id}"))
        if not item.continuity_prompt_present:
            ok = False
            issues.append(_issue("video motion review continuity prompt missing", f"{path.as_posix()}:{item.item_id}"))
        if not Path(item.image_path).exists():
            ok = False
            issues.append(_issue("video motion review image missing", item.image_path))
        if not Path(item.request_preview_path).exists():
            ok = False
            issues.append(_issue("video motion review request preview missing", item.request_preview_path))
    for message, gap_path in find_video_motion_review_gaps(story_dir, review):
        ok = False
        issues.append(_issue(message, gap_path))
    checks["video_motion_review"] = "passed" if ok else "failed"


def _check_review_packet(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealVideoPreflightIssue],
) -> None:
    path = story_dir / "review" / "review_packet.json"
    if not path.exists():
        checks["review_packet"] = "failed"
        issues.append(_issue("review packet missing", path.as_posix()))
        return
    try:
        packet = ReviewPacket.model_validate(read_json(path))
    except Exception as exc:
        checks["review_packet"] = "failed"
        issues.append(_issue(f"review packet schema validation failed: {exc}", path.as_posix()))
        return
    ok = True
    for item in packet.items:
        if item.status != "approved":
            ok = False
            issues.append(_issue(f"review packet item is {item.status}", f"{path.as_posix()}:{item.item_id}"))
        for artifact_path in item.artifact_paths:
            if not Path(artifact_path).exists():
                ok = False
                issues.append(_issue("review packet artifact missing", artifact_path))
    for message, gap_path in find_review_packet_dry_run_gaps(story_dir, packet):
        ok = False
        issues.append(_issue(message, gap_path))
    checks["review_packet"] = "passed" if ok else "failed"


def _hash_path(hasher: hashlib._Hash, path: Path) -> None:
    hasher.update(path.as_posix().encode("utf-8"))
    hasher.update(b"\0")
    if not path.exists():
        hasher.update(b"<missing>")
        hasher.update(b"\0")
        return
    hasher.update(path.read_bytes())
    hasher.update(b"\0")


def _artifact_fingerprint(story_dir: Path) -> str:
    hasher = hashlib.sha256()
    paths = [story_dir / relative_path for relative_path in FINGERPRINT_PATHS]

    seedance_jobs_path = story_dir / "seedance_dry_run" / "jobs.json"
    if seedance_jobs_path.exists():
        try:
            for job in [SeedanceDryRunJob.model_validate(item) for item in read_json(seedance_jobs_path)]:
                paths.append(Path(job.image_path))
                paths.append(Path(job.request_preview_path))
        except Exception:
            pass

    motion_review_path = story_dir / "review" / "video_motion_review.json"
    if motion_review_path.exists():
        try:
            review = VideoMotionReview.model_validate(read_json(motion_review_path))
            for item in review.items:
                paths.append(Path(item.image_path))
                paths.append(Path(item.request_preview_path))
        except Exception:
            pass

    unique_paths = sorted({path.as_posix(): path for path in paths}.items())
    for _path_key, path in unique_paths:
        _hash_path(hasher, path)
    return f"sha256:{hasher.hexdigest()}"


def build_real_video_preflight_report(story_dir: Path) -> RealVideoPreflightReport:
    checks: dict[str, str] = {}
    issues: list[RealVideoPreflightIssue] = []

    _check_file(story_dir / "02_storyboard.json", checks, issues, "storyboard")
    _check_video_jobs(story_dir, checks, issues)
    _check_seedance_dry_run(story_dir, checks, issues)
    _check_video_motion_review(story_dir, checks, issues)
    _check_review_packet(story_dir, checks, issues)

    ok = not issues
    return RealVideoPreflightReport(
        ok=ok,
        story_dir=story_dir.as_posix(),
        seedance_dry_run_jobs_path=(story_dir / "seedance_dry_run" / "jobs.json").as_posix(),
        video_motion_review_path=(story_dir / "review" / "video_motion_review.json").as_posix(),
        review_packet_path=(story_dir / "review" / "review_packet.json").as_posix(),
        artifact_fingerprint=_artifact_fingerprint(story_dir),
        checks=checks,
        issues=issues,
        next_step="STOP_BEFORE_REAL_VIDEO_GENERATION" if ok else "BLOCKED",
        stop_reason=(
            "Ready to generate real videos; stop here and ask the user before invoking Seedance."
            if ok
            else "Real video generation is blocked until all preflight checks pass."
        ),
    )

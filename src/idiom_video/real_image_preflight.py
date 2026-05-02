from __future__ import annotations

from pathlib import Path

from idiom_video.comfyui_smoke import build_comfyui_smoke_report
from idiom_video.review_packet import find_review_packet_dry_run_gaps
from idiom_video.schemas import (
    ComfyUISmokeCheckReport,
    RealImagePreflightIssue,
    RealImagePreflightReport,
    ReviewPacket,
)
from idiom_video.utils.json_io import read_json


def _issue(message: str, path: str | None = None) -> RealImagePreflightIssue:
    return RealImagePreflightIssue(message=message, path=path)


def _check_file(path: Path, checks: dict[str, str], issues: list[RealImagePreflightIssue], check_name: str) -> None:
    if path.exists():
        checks[check_name] = "passed"
        return
    checks[check_name] = "failed"
    issues.append(_issue("required preflight artifact missing", path.as_posix()))


def _check_prompt_quality(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealImagePreflightIssue],
) -> None:
    report_path = story_dir / "quality_reports" / "prompt_quality.json"
    if not report_path.exists():
        checks["prompt_quality"] = "failed"
        issues.append(_issue("prompt quality report missing", report_path.as_posix()))
        return
    report = read_json(report_path)
    if report.get("ok") is True:
        checks["prompt_quality"] = "passed"
        return
    checks["prompt_quality"] = "failed"
    issues.append(_issue("prompt quality must pass before real image generation", report_path.as_posix()))


def _check_review_packet(
    story_dir: Path,
    checks: dict[str, str],
    issues: list[RealImagePreflightIssue],
) -> None:
    packet_path = story_dir / "review" / "review_packet.json"
    if not packet_path.exists():
        checks["review_packet"] = "failed"
        issues.append(_issue("review packet missing", packet_path.as_posix()))
        return
    packet = ReviewPacket.model_validate(read_json(packet_path))
    packet_ok = True
    for item in packet.items:
        if item.status != "approved":
            packet_ok = False
            issues.append(_issue(f"review packet item is {item.status}", f"{packet_path.as_posix()}:{item.item_id}"))
        for artifact_path in item.artifact_paths:
            if not Path(artifact_path).exists():
                packet_ok = False
                issues.append(_issue("review packet artifact missing", artifact_path))
    for message, path in find_review_packet_dry_run_gaps(story_dir, packet):
        packet_ok = False
        issues.append(_issue(message, path))
    checks["review_packet"] = "passed" if packet_ok else "failed"


def build_real_image_preflight_report(
    story_dir: Path,
    workflow_path: Path,
    manifest_path: Path,
    smoke_report: ComfyUISmokeCheckReport | None = None,
) -> RealImagePreflightReport:
    checks: dict[str, str] = {}
    issues: list[RealImagePreflightIssue] = []
    smoke_report_path = story_dir / "quality_reports" / "comfyui_smoke_check.json"

    for check_name, relative_path in [
        ("image_prompts", "03_image_prompts.json"),
        ("image_jobs", "04_image_jobs.json"),
    ]:
        _check_file(story_dir / relative_path, checks, issues, check_name)

    _check_prompt_quality(story_dir, checks, issues)
    _check_review_packet(story_dir, checks, issues)

    smoke_report = smoke_report or build_comfyui_smoke_report(story_dir, workflow_path, manifest_path)
    checks["comfyui_smoke"] = "passed" if smoke_report.ok else "failed"
    if not smoke_report.ok:
        issues.append(
            _issue(
                "ComfyUI smoke check must pass before real image generation",
                smoke_report_path.as_posix(),
            )
        )
        for smoke_issue in smoke_report.issues:
            issues.append(_issue(smoke_issue.message, smoke_issue.path))

    ok = not issues
    return RealImagePreflightReport(
        ok=ok,
        story_dir=story_dir.as_posix(),
        workflow_path=workflow_path.as_posix(),
        manifest_path=manifest_path.as_posix(),
        smoke_report_path=smoke_report_path.as_posix(),
        checks=checks,
        issues=issues,
        next_step="STOP_BEFORE_REAL_IMAGE_GENERATION" if ok else "BLOCKED",
        stop_reason=(
            "Ready to generate real images; stop here and ask the user before invoking ComfyUI."
            if ok
            else "Real image generation is blocked until all preflight checks pass."
        ),
    )

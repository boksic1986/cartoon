from __future__ import annotations

import math
from pathlib import Path

from idiom_video.real_video_preflight import build_real_video_preflight_report
from idiom_video.schemas import (
    RealVideoPreflightReport,
    SeedanceCostEstimate,
    SeedanceDryRunJob,
    SeedanceSubmitPlan,
    SeedanceSubmitPlanItem,
)
from idiom_video.utils.json_io import read_json


SENSITIVE_MARKERS = (
    "authorization",
    "bearer ",
    "sk-",
    "api_key",
    "api-key",
    "x-api-key",
    "account_id",
    "account id",
)


def _load_preflight_report(story_dir: Path) -> RealVideoPreflightReport:
    return RealVideoPreflightReport.model_validate(read_json(story_dir / "quality_reports" / "real_video_preflight.json"))


def _load_cost_estimate(story_dir: Path) -> SeedanceCostEstimate:
    return SeedanceCostEstimate.model_validate(read_json(story_dir / "quality_reports" / "seedance_cost_estimate.json"))


def _load_seedance_dry_run_jobs(story_dir: Path) -> list[SeedanceDryRunJob]:
    return [
        SeedanceDryRunJob.model_validate(item)
        for item in read_json(story_dir / "seedance_dry_run" / "jobs.json")
    ]


def _assert_no_sensitive_strings(items: list[SeedanceSubmitPlanItem]) -> None:
    for item in items:
        payload = item.model_dump(mode="json")
        for field_name, value in payload.items():
            if not isinstance(value, str):
                continue
            lowered = value.lower()
            if any(marker in lowered for marker in SENSITIVE_MARKERS):
                raise ValueError(f"sensitive string detected in Seedance submit plan field: {field_name}")


def validate_seedance_submit_plan_current(story_dir: Path, plan: SeedanceSubmitPlan) -> list[str]:
    issues: list[str] = []
    current_preflight = build_real_video_preflight_report(story_dir)
    if not current_preflight.ok:
        issues.append("current real video preflight no longer passes")
    if current_preflight.artifact_fingerprint != plan.preflight_artifact_fingerprint:
        issues.append("Seedance submit plan is stale; rerun prepare-seedance-submit")
    cost = _load_cost_estimate(story_dir)
    if cost.estimated_total_cost > plan.max_cost:
        issues.append("current Seedance cost estimate exceeds submit plan max cost")
    return issues


def build_seedance_submit_plan(
    story_dir: Path,
    *,
    max_cost: float,
    confirm_external_call: bool,
    execute_real: bool = False,
) -> SeedanceSubmitPlan:
    if not math.isfinite(max_cost) or max_cost <= 0:
        raise ValueError("--max-cost must be a finite positive number")
    if execute_real:
        raise ValueError("real Seedance submission is not implemented in this phase")
    if not confirm_external_call:
        raise ValueError("--confirm-external-call is required before preparing Seedance submit plan")
    story_path = story_dir
    resolved_story_path = story_dir.resolve()
    preflight_path = story_path / "quality_reports" / "real_video_preflight.json"
    cost_path = story_path / "quality_reports" / "seedance_cost_estimate.json"
    saved_preflight = _load_preflight_report(story_path)
    current_preflight = build_real_video_preflight_report(story_path)
    if not saved_preflight.ok:
        raise ValueError("saved real video preflight report is not ok")
    if not current_preflight.ok:
        raise ValueError("current real video preflight no longer passes")
    if saved_preflight.artifact_fingerprint != current_preflight.artifact_fingerprint:
        raise ValueError("saved real video preflight report is stale; rerun real-video-preflight")
    cost = _load_cost_estimate(story_path)
    if cost.estimated_total_cost > max_cost:
        raise ValueError(f"estimated Seedance cost {cost.estimated_total_cost} {cost.currency} exceeds max cost {max_cost}")
    dry_run_jobs = _load_seedance_dry_run_jobs(story_path)
    items = [
        SeedanceSubmitPlanItem(
            source_job_id=job.source_job_id,
            scene_id=job.scene_id,
            image_path=job.image_path,
            prompt=job.prompt,
            duration_seconds=job.duration_seconds,
            intended_output_path=job.intended_output_path,
            request_preview_path=job.request_preview_path,
            status="ready",
        )
        for job in dry_run_jobs
    ]
    _assert_no_sensitive_strings(items)
    return SeedanceSubmitPlan(
        ok=True,
        provider="seedance",
        dry_run=True,
        execute_real_requested=execute_real,
        external_call_confirmed=confirm_external_call,
        story_dir=resolved_story_path.as_posix(),
        preflight_report_path=preflight_path.as_posix(),
        preflight_artifact_fingerprint=current_preflight.artifact_fingerprint,
        cost_estimate_path=cost_path.as_posix(),
        currency=cost.currency,
        estimated_total_cost=cost.estimated_total_cost,
        max_cost=max_cost,
        item_count=len(items),
        items=items,
        next_step="STOP_BEFORE_REAL_SEEDANCE_SUBMIT",
        stop_reason="Submit plan is ready; stop here before any real Seedance API call.",
        notes=[
            "Offline submit plan only; this command does not call Seedance or any external service.",
            "Provider credentials, sensitive request headers, and account identifiers must never be written to this file.",
            "Real submission must be implemented in a later phase with explicit human confirmation and mock HTTP tests first.",
        ],
    )

from __future__ import annotations

import hashlib
from pathlib import Path

from idiom_video.schemas import (
    SeedanceSubmitPlan,
    SeedanceTaskBatch,
    SeedanceTaskRecord,
    SeedanceTaskResult,
    SeedanceTaskResults,
    VideoClip,
)
from idiom_video.seedance_submit import SENSITIVE_MARKERS, validate_seedance_submit_plan_current
from idiom_video.utils.json_io import read_json, write_json


def submit_plan_fingerprint(submit_plan_path: Path) -> str:
    resolved_path = submit_plan_path.resolve()
    hasher = hashlib.sha256()
    hasher.update(resolved_path.as_posix().encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(resolved_path.read_bytes())
    return f"sha256:{hasher.hexdigest()}"


def _load_submit_plan(story_dir: Path) -> SeedanceSubmitPlan:
    return SeedanceSubmitPlan.model_validate(read_json(story_dir / "seedance_submit" / "submit_plan.json"))


def _assert_no_sensitive_payload(value: str, *, field_name: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError(f"sensitive string detected in Seedance task field: {field_name}")


def _validate_submit_plan_for_tasks(story_dir: Path, plan: SeedanceSubmitPlan) -> None:
    issues = validate_seedance_submit_plan_current(story_dir, plan)
    if issues:
        raise ValueError("; ".join(issues))
    for item in plan.items:
        for field_name, value in item.model_dump(mode="json").items():
            if isinstance(value, str):
                _assert_no_sensitive_payload(value, field_name=field_name)


def submit_seedance_tasks_mock(story_dir: Path) -> SeedanceTaskBatch:
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submit_plan_path = story_path / "seedance_submit" / "submit_plan.json"
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    fingerprint = submit_plan_fingerprint(submit_plan_path)
    records: list[SeedanceTaskRecord] = []
    for index, item in enumerate(plan.items, start=1):
        task_id = f"seedance_mock_{index:02d}_{item.scene_id}"
        request_path = tasks_dir / f"{item.scene_id}.submit_request.json"
        response_path = tasks_dir / f"{item.scene_id}.submit_response.json"
        request_payload = {
            "provider": "seedance",
            "client": "mock",
            "dry_run": True,
            "task_id": task_id,
            "source_job_id": item.source_job_id,
            "scene_id": item.scene_id,
            "image_path": item.image_path,
            "prompt": item.prompt,
            "duration_seconds": item.duration_seconds,
            "intended_output_path": item.intended_output_path,
        }
        response_payload = {
            "provider": "seedance",
            "client": "mock",
            "dry_run": True,
            "task_id": task_id,
            "status": "submitted",
            "message": "Mock Seedance task accepted locally; no external service was called.",
        }
        write_json(request_path, request_payload)
        write_json(response_path, response_payload)
        records.append(
            SeedanceTaskRecord(
                task_id=task_id,
                source_job_id=item.source_job_id,
                scene_id=item.scene_id,
                image_path=item.image_path,
                prompt=item.prompt,
                duration_seconds=item.duration_seconds,
                intended_output_path=item.intended_output_path,
                request_preview_path=item.request_preview_path,
                submit_request_path=request_path.as_posix(),
                submit_response_path=response_path.as_posix(),
                status="submitted",
            )
        )
    batch = SeedanceTaskBatch(
        ok=True,
        provider="seedance",
        client="mock",
        dry_run=True,
        submit_plan_path=submit_plan_path.as_posix(),
        submit_plan_fingerprint=fingerprint,
        task_count=len(records),
        tasks=records,
        next_step="MOCK_POLL_SEEDANCE_TASKS",
        notes=["Mock task submission only; no real Seedance API call was made."],
    )
    write_json(tasks_dir / "submissions.json", batch)
    return batch


def poll_seedance_tasks_mock(story_dir: Path) -> SeedanceTaskResults:
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submissions_path = tasks_dir / "submissions.json"
    batch = SeedanceTaskBatch.model_validate(read_json(submissions_path))
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    current_fingerprint = submit_plan_fingerprint(story_path / "seedance_submit" / "submit_plan.json")
    if batch.submit_plan_fingerprint != current_fingerprint:
        raise ValueError("Seedance task submissions are stale; rerun submit-seedance-tasks")
    results: list[SeedanceTaskResult] = []
    clips: list[VideoClip] = []
    for task in batch.tasks:
        poll_path = tasks_dir / f"{task.scene_id}.poll_response.json"
        download_path = tasks_dir / f"{task.scene_id}.download_response.json"
        output_path = story_path / "videos" / f"{task.scene_id}.seedance_mock.txt"
        write_json(
            poll_path,
            {
                "provider": "seedance",
                "client": "mock",
                "dry_run": True,
                "task_id": task.task_id,
                "status": "succeeded",
            },
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    "Mock Seedance video placeholder.",
                    f"task_id={task.task_id}",
                    f"scene_id={task.scene_id}",
                    f"duration_seconds={task.duration_seconds}",
                    "No external service was called.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        write_json(
            download_path,
            {
                "provider": "seedance",
                "client": "mock",
                "dry_run": True,
                "task_id": task.task_id,
                "output_path": output_path.as_posix(),
                "status": "downloaded",
            },
        )
        results.append(
            SeedanceTaskResult(
                task_id=task.task_id,
                source_job_id=task.source_job_id,
                scene_id=task.scene_id,
                status="succeeded",
                output_path=output_path.as_posix(),
                poll_response_path=poll_path.as_posix(),
                download_response_path=download_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_mock",
            )
        )
        clips.append(
            VideoClip(
                clip_id=f"seedance_mock_{task.scene_id}",
                scene_id=task.scene_id,
                path=output_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_mock",
            )
        )
    task_results = SeedanceTaskResults(
        ok=True,
        provider="seedance",
        client="mock",
        dry_run=True,
        submit_plan_path=batch.submit_plan_path,
        submit_plan_fingerprint=batch.submit_plan_fingerprint,
        submissions_path=submissions_path.as_posix(),
        task_count=len(results),
        results=results,
        next_step="MOCK_SEEDANCE_COMPLETE",
        notes=["Mock polling and download only; no real Seedance API call was made."],
    )
    write_json(tasks_dir / "results.json", task_results)
    write_json(story_path / "videos" / "seedance_clips.json", clips)
    return task_results

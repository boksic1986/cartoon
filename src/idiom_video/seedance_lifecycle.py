from __future__ import annotations

import hashlib
import ipaddress
import os
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from idiom_video.schemas import (
    SeedanceClientDownloadRequest,
    SeedanceClientPollRequest,
    SeedanceClientSubmitRequest,
    SeedanceSubmitPlan,
    SeedanceTaskBatch,
    SeedanceTaskRecord,
    SeedanceTaskResult,
    SeedanceTaskResults,
    VideoClip,
)
from idiom_video.providers.seedance_client import MockSeedanceHttpTransport, RealSeedanceHttpTransport, SeedanceApiClient
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


def _resolve_api_key(api_key: str | None = None) -> str:
    key = api_key or os.getenv("ARK_API_KEY") or os.getenv("SEEDANCE_API_KEY") or os.getenv("BYTEPLUS_ARK_API_KEY")
    if not key:
        raise ValueError("ARK_API_KEY or SEEDANCE_API_KEY is required for real Seedance calls")
    return key


def _load_image_url_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError("--image-url-map must point to a JSON object")
    return {str(key): str(value) for key, value in payload.items()}


def _assert_public_image_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("public image URL must use http or https and include a host")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("public image URL must not point to localhost or local-only hosts")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return url
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
        raise ValueError("public image URL must not point to private, loopback, or reserved IP addresses")
    return url


def _image_url_for_item(item, *, image_url_map: dict[str, str], image_base_url: str | None) -> str | None:
    if item.scene_id in image_url_map:
        return _assert_public_image_url(image_url_map[item.scene_id])
    if item.source_job_id in image_url_map:
        return _assert_public_image_url(image_url_map[item.source_job_id])
    if image_base_url:
        return _assert_public_image_url(urljoin(image_base_url.rstrip("/") + "/", Path(item.image_path).name))
    return None


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


def submit_seedance_tasks_mock_http(story_dir: Path) -> SeedanceTaskBatch:
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submit_plan_path = story_path / "seedance_submit" / "submit_plan.json"
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    fingerprint = submit_plan_fingerprint(submit_plan_path)
    client = SeedanceApiClient(MockSeedanceHttpTransport())
    records: list[SeedanceTaskRecord] = []
    for item in plan.items:
        request_path = tasks_dir / f"{item.scene_id}.mock_http.submit_request.json"
        response_path = tasks_dir / f"{item.scene_id}.mock_http.submit_response.json"
        request = SeedanceClientSubmitRequest(
            source_job_id=item.source_job_id,
            scene_id=item.scene_id,
            image_path=item.image_path,
            prompt=item.prompt,
            duration_seconds=item.duration_seconds,
            intended_output_path=item.intended_output_path,
        )
        response = client.submit(request)
        write_json(request_path, request)
        write_json(response_path, response)
        records.append(
            SeedanceTaskRecord(
                task_id=response.task_id,
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
        client="mock_http",
        dry_run=True,
        submit_plan_path=submit_plan_path.as_posix(),
        submit_plan_fingerprint=fingerprint,
        task_count=len(records),
        tasks=records,
        next_step="MOCK_HTTP_POLL_SEEDANCE_TASKS",
        notes=[
            "Seedance provider dry-run via local mock HTTP contract; no network request was made.",
            "This artifact is a request/response contract rehearsal, not a real Seedance task ledger.",
        ],
    )
    write_json(tasks_dir / "submissions.json", batch)
    return batch


def submit_seedance_tasks_real(
    story_dir: Path,
    *,
    api_key: str | None = None,
    base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3",
    model_name: str = "seedance-1-0-pro-250528",
    ratio: str = "9:16",
    resolution: str = "720p",
    image_url_map_path: Path | None = None,
    image_base_url: str | None = None,
    max_real_tasks: int = 1,
    allow_text_only: bool = False,
) -> SeedanceTaskBatch:
    if max_real_tasks <= 0:
        raise ValueError("--max-real-tasks must be positive")
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submit_plan_path = story_path / "seedance_submit" / "submit_plan.json"
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    fingerprint = submit_plan_fingerprint(submit_plan_path)
    image_url_map = _load_image_url_map(image_url_map_path)
    client = SeedanceApiClient(
        RealSeedanceHttpTransport(
            api_key=_resolve_api_key(api_key),
            base_url=base_url,
            model_name=model_name,
            ratio=ratio,
            resolution=resolution,
        )
    )
    records: list[SeedanceTaskRecord] = []
    for item in plan.items[:max_real_tasks]:
        image_url = _image_url_for_item(item, image_url_map=image_url_map, image_base_url=image_base_url)
        if not image_url and not allow_text_only:
            raise ValueError("public image URL is required for real Seedance image-to-video; pass --image-url-map/--image-base-url or --allow-text-only")
        request_path = tasks_dir / f"{item.scene_id}.real.submit_request.json"
        response_path = tasks_dir / f"{item.scene_id}.real.submit_response.json"
        request_payload = SeedanceClientSubmitRequest(
            client="seedance_real",
            dry_run=False,
            source_job_id=item.source_job_id,
            scene_id=item.scene_id,
            image_path=item.image_path,
            image_url=image_url,
            prompt=item.prompt,
            duration_seconds=item.duration_seconds,
            intended_output_path=item.intended_output_path,
        )
        response = client.submit(request_payload)
        write_json(request_path, request_payload)
        write_json(response_path, response)
        records.append(
            SeedanceTaskRecord(
                task_id=response.task_id,
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
        client="seedance_real",
        dry_run=False,
        submit_plan_path=submit_plan_path.as_posix(),
        submit_plan_fingerprint=fingerprint,
        task_count=len(records),
        tasks=records,
        next_step="POLL_SEEDANCE_REAL_TASKS",
        notes=[
            "Real Seedance submit call was requested explicitly.",
            "Request/response artifacts omit provider credentials.",
        ],
    )
    write_json(tasks_dir / "submissions.json", batch)
    return batch


def poll_seedance_tasks_mock(story_dir: Path) -> SeedanceTaskResults:
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submissions_path = tasks_dir / "submissions.json"
    batch = SeedanceTaskBatch.model_validate(read_json(submissions_path))
    if batch.client != "mock":
        raise ValueError("Seedance mock polling requires mock submissions; rerun submit-seedance-tasks --provider mock")
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


def poll_seedance_tasks_mock_http(story_dir: Path) -> SeedanceTaskResults:
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submissions_path = tasks_dir / "submissions.json"
    batch = SeedanceTaskBatch.model_validate(read_json(submissions_path))
    if batch.client != "mock_http":
        raise ValueError("Seedance mock HTTP polling requires mock HTTP submissions; rerun submit-seedance-tasks --provider seedance --dry-run")
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    current_fingerprint = submit_plan_fingerprint(story_path / "seedance_submit" / "submit_plan.json")
    if batch.submit_plan_fingerprint != current_fingerprint:
        raise ValueError("Seedance task submissions are stale; rerun submit-seedance-tasks")
    client = SeedanceApiClient(MockSeedanceHttpTransport())
    results: list[SeedanceTaskResult] = []
    clips: list[VideoClip] = []
    for task in batch.tasks:
        poll_request_path = tasks_dir / f"{task.scene_id}.mock_http.poll_request.json"
        poll_response_path = tasks_dir / f"{task.scene_id}.mock_http.poll_response.json"
        download_request_path = tasks_dir / f"{task.scene_id}.mock_http.download_request.json"
        download_response_path = tasks_dir / f"{task.scene_id}.mock_http.download_response.json"
        output_path = story_path / "videos" / f"{task.scene_id}.seedance_mock_http.txt"
        poll_request = SeedanceClientPollRequest(task_id=task.task_id, scene_id=task.scene_id)
        poll_response = client.poll(poll_request)
        write_json(poll_request_path, poll_request)
        write_json(poll_response_path, poll_response)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(
                [
                    "Mock HTTP Seedance video placeholder.",
                    f"task_id={task.task_id}",
                    f"scene_id={task.scene_id}",
                    f"duration_seconds={task.duration_seconds}",
                    "No network request was made.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        download_request = SeedanceClientDownloadRequest(task_id=task.task_id, scene_id=task.scene_id)
        download_response = client.download(download_request, output_path=output_path.as_posix())
        write_json(download_request_path, download_request)
        write_json(download_response_path, download_response)
        results.append(
            SeedanceTaskResult(
                task_id=task.task_id,
                source_job_id=task.source_job_id,
                scene_id=task.scene_id,
                status="succeeded",
                output_path=output_path.as_posix(),
                poll_request_path=poll_request_path.as_posix(),
                poll_response_path=poll_response_path.as_posix(),
                download_request_path=download_request_path.as_posix(),
                download_response_path=download_response_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_mock_http",
            )
        )
        clips.append(
            VideoClip(
                clip_id=f"seedance_mock_http_{task.scene_id}",
                scene_id=task.scene_id,
                path=output_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_mock_http",
            )
        )
    task_results = SeedanceTaskResults(
        ok=True,
        provider="seedance",
        client="mock_http",
        dry_run=True,
        submit_plan_path=batch.submit_plan_path,
        submit_plan_fingerprint=batch.submit_plan_fingerprint,
        submissions_path=submissions_path.as_posix(),
        task_count=len(results),
        results=results,
        next_step="MOCK_HTTP_SEEDANCE_COMPLETE",
        notes=[
            "Seedance provider polling/download dry-run via local mock HTTP contract; no network request was made.",
            "Generated video files are placeholders for contract review only.",
        ],
    )
    write_json(tasks_dir / "results.json", task_results)
    write_json(story_path / "videos" / "seedance_clips.json", clips)
    return task_results


def poll_seedance_tasks_real(
    story_dir: Path,
    *,
    api_key: str | None = None,
    base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3",
    model_name: str = "seedance-1-0-pro-250528",
    ratio: str = "9:16",
    resolution: str = "720p",
    poll_interval_seconds: float = 5.0,
    max_poll_attempts: int = 60,
) -> SeedanceTaskResults:
    if poll_interval_seconds < 0:
        raise ValueError("--poll-interval-seconds must be non-negative")
    if max_poll_attempts <= 0:
        raise ValueError("--max-poll-attempts must be positive")
    story_path = story_dir
    tasks_dir = story_path / "seedance_tasks"
    submissions_path = tasks_dir / "submissions.json"
    batch = SeedanceTaskBatch.model_validate(read_json(submissions_path))
    if batch.client != "seedance_real":
        raise ValueError("real Seedance polling requires real Seedance submissions; rerun submit-seedance-tasks --provider seedance --execute-real")
    plan = _load_submit_plan(story_path)
    _validate_submit_plan_for_tasks(story_path, plan)
    current_fingerprint = submit_plan_fingerprint(story_path / "seedance_submit" / "submit_plan.json")
    if batch.submit_plan_fingerprint != current_fingerprint:
        raise ValueError("Seedance task submissions are stale; rerun submit-seedance-tasks")
    client = SeedanceApiClient(
        RealSeedanceHttpTransport(
            api_key=_resolve_api_key(api_key),
            base_url=base_url,
            model_name=model_name,
            ratio=ratio,
            resolution=resolution,
        )
    )
    results: list[SeedanceTaskResult] = []
    clips: list[VideoClip] = []
    for task in batch.tasks:
        poll_request_path = tasks_dir / f"{task.scene_id}.real.poll_request.json"
        poll_response_path = tasks_dir / f"{task.scene_id}.real.poll_response.json"
        download_request_path = tasks_dir / f"{task.scene_id}.real.download_request.json"
        download_response_path = tasks_dir / f"{task.scene_id}.real.download_response.json"
        output_path = story_path / "videos" / f"{task.scene_id}.seedance_real.mp4"
        last_poll_response = None
        poll_request = SeedanceClientPollRequest(client="seedance_real", dry_run=False, task_id=task.task_id, scene_id=task.scene_id)
        write_json(poll_request_path, poll_request)
        for attempt in range(max_poll_attempts):
            last_poll_response = client.poll(poll_request)
            write_json(poll_response_path, last_poll_response)
            if last_poll_response.status == "succeeded":
                break
            if last_poll_response.status == "failed":
                raise ValueError(f"Seedance task failed: {task.task_id}: {last_poll_response.error_message or 'unknown error'}")
            if attempt < max_poll_attempts - 1 and poll_interval_seconds:
                time.sleep(poll_interval_seconds)
        if last_poll_response is None or last_poll_response.status != "succeeded":
            raise ValueError(f"Seedance task did not complete within max poll attempts: {task.task_id}")
        download_request = SeedanceClientDownloadRequest(client="seedance_real", dry_run=False, task_id=task.task_id, scene_id=task.scene_id)
        write_json(download_request_path, download_request)
        download_response = client.download(download_request, output_path=output_path.as_posix())
        write_json(download_response_path, download_response)
        results.append(
            SeedanceTaskResult(
                task_id=task.task_id,
                source_job_id=task.source_job_id,
                scene_id=task.scene_id,
                status="succeeded",
                output_path=output_path.as_posix(),
                poll_request_path=poll_request_path.as_posix(),
                poll_response_path=poll_response_path.as_posix(),
                download_request_path=download_request_path.as_posix(),
                download_response_path=download_response_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_real",
            )
        )
        clips.append(
            VideoClip(
                clip_id=f"seedance_real_{task.scene_id}",
                scene_id=task.scene_id,
                path=output_path.as_posix(),
                duration_seconds=task.duration_seconds,
                provider="seedance_real",
            )
        )
    task_results = SeedanceTaskResults(
        ok=True,
        provider="seedance",
        client="seedance_real",
        dry_run=False,
        submit_plan_path=batch.submit_plan_path,
        submit_plan_fingerprint=batch.submit_plan_fingerprint,
        submissions_path=submissions_path.as_posix(),
        task_count=len(results),
        results=results,
        next_step="SEEDANCE_REAL_COMPLETE",
        notes=[
            "Real Seedance polling/download was requested explicitly.",
            "Provider credentials and temporary remote media links are not written to JSON artifacts.",
        ],
    )
    write_json(tasks_dir / "results.json", task_results)
    write_json(story_path / "videos" / "seedance_clips.json", clips)
    return task_results

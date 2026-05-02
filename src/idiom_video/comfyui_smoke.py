from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from idiom_video.schemas import (
    ComfyUIDryRunJob,
    ComfyUISmokeCheckIssue,
    ComfyUISmokeCheckReport,
    ModelManifest,
    ModelManifestEntry,
)
from idiom_video.utils.json_io import read_json


PLACEHOLDER_MARKERS = ("placeholder", "review_required")


def _issue(message: str, path: str | None = None) -> ComfyUISmokeCheckIssue:
    return ComfyUISmokeCheckIssue(message=message, path=path)


def _contains_placeholder_marker(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def _path_for_compare(path: str | Path) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().as_posix().lower()
    except OSError:
        return candidate.as_posix().lower()


def _manifest_entry_has_placeholder(entry: ModelManifestEntry) -> bool:
    searchable = {
        "name": entry.name,
        "local_path": entry.local_path,
        "source": entry.source,
        "license": entry.license,
    }
    return _contains_placeholder_marker(searchable)


def build_comfyui_smoke_report(
    story_dir: Path,
    workflow_path: Path,
    manifest_path: Path,
    allow_placeholders: bool = False,
) -> ComfyUISmokeCheckReport:
    checks: dict[str, str] = {}
    issues: list[ComfyUISmokeCheckIssue] = []
    dry_run_jobs_path = story_dir / "comfyui_dry_run" / "jobs.json"

    workflow_data: Any | None = None
    if not workflow_path.exists():
        checks["workflow_exists"] = "failed"
        checks["workflow_json"] = "failed"
        checks["workflow_review"] = "failed"
        issues.append(_issue("ComfyUI workflow missing", workflow_path.as_posix()))
    else:
        checks["workflow_exists"] = "passed"
        try:
            workflow_data = read_json(workflow_path)
            checks["workflow_json"] = "passed"
        except Exception as exc:
            checks["workflow_json"] = "failed"
            issues.append(_issue(f"ComfyUI workflow is not valid JSON: {exc}", workflow_path.as_posix()))
        workflow_payload = {"path": workflow_path.as_posix(), "data": workflow_data}
        if workflow_data is not None and _contains_placeholder_marker(workflow_payload) and not allow_placeholders:
            checks["workflow_review"] = "failed"
            issues.append(_issue("ComfyUI workflow still contains placeholder markers", workflow_path.as_posix()))
        elif workflow_data is None:
            checks["workflow_review"] = "failed"
        else:
            checks["workflow_review"] = "passed"

    manifest: ModelManifest | None = None
    if not manifest_path.exists():
        checks["models_manifest_schema"] = "failed"
        checks["models_manifest_readiness"] = "failed"
        issues.append(_issue("models manifest missing", manifest_path.as_posix()))
    else:
        try:
            manifest = ModelManifest.model_validate(read_json(manifest_path))
            checks["models_manifest_schema"] = "passed"
        except Exception as exc:
            checks["models_manifest_schema"] = "failed"
            checks["models_manifest_readiness"] = "failed"
            issues.append(_issue(f"models manifest schema validation failed: {exc}", manifest_path.as_posix()))
        if manifest is not None:
            manifest_ready = True
            for index, entry in enumerate(manifest.models):
                entry_path = f"{manifest_path.as_posix()}:models[{index}]"
                if _manifest_entry_has_placeholder(entry) and not allow_placeholders:
                    manifest_ready = False
                    issues.append(_issue("model manifest entry still contains placeholder markers", entry_path))
                if entry.commercial_use_allowed is None:
                    manifest_ready = False
                    issues.append(_issue("model manifest entry needs explicit commercial_use_allowed", entry_path))
            checks["models_manifest_readiness"] = "passed" if manifest_ready else "failed"

    dry_run_jobs: list[ComfyUIDryRunJob] | None = None
    if not dry_run_jobs_path.exists():
        checks["dry_run_jobs_schema"] = "failed"
        checks["dry_run_preview_files"] = "failed"
        checks["dry_run_workflow_match"] = "failed"
        issues.append(_issue("ComfyUI dry-run jobs missing", dry_run_jobs_path.as_posix()))
    else:
        try:
            dry_run_jobs = [ComfyUIDryRunJob.model_validate(item) for item in read_json(dry_run_jobs_path)]
            checks["dry_run_jobs_schema"] = "passed"
            if not dry_run_jobs:
                checks["dry_run_jobs_schema"] = "failed"
                issues.append(_issue("ComfyUI dry-run jobs must not be empty", dry_run_jobs_path.as_posix()))
        except Exception as exc:
            checks["dry_run_jobs_schema"] = "failed"
            checks["dry_run_preview_files"] = "failed"
            checks["dry_run_workflow_match"] = "failed"
            issues.append(_issue(f"ComfyUI dry-run jobs schema validation failed: {exc}", dry_run_jobs_path.as_posix()))

    if dry_run_jobs is not None:
        preview_missing = False
        workflow_mismatch = False
        expected_workflow = _path_for_compare(workflow_path)
        for index, job in enumerate(dry_run_jobs):
            if not Path(job.request_preview_path).exists():
                preview_missing = True
                issues.append(_issue("ComfyUI dry-run request preview missing", job.request_preview_path))
            if _path_for_compare(job.workflow_path) != expected_workflow:
                workflow_mismatch = True
                issues.append(
                    _issue(
                        "ComfyUI dry-run workflow does not match requested workflow",
                        f"{dry_run_jobs_path.as_posix()}[{index}]",
                    )
                )
        checks["dry_run_preview_files"] = "failed" if preview_missing else "passed"
        checks["dry_run_workflow_match"] = "failed" if workflow_mismatch else "passed"

    return ComfyUISmokeCheckReport(
        ok=not issues,
        workflow_path=workflow_path.as_posix(),
        manifest_path=manifest_path.as_posix(),
        dry_run_jobs_path=dry_run_jobs_path.as_posix(),
        checks=checks,
        issues=issues,
    )

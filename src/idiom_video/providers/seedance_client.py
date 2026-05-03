from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol
from urllib import error, request

from idiom_video.schemas import (
    SeedanceClientDownloadRequest,
    SeedanceClientDownloadResponse,
    SeedanceClientPollRequest,
    SeedanceClientPollResponse,
    SeedanceClientSubmitRequest,
    SeedanceClientSubmitResponse,
)
from idiom_video.seedance_submit import SENSITIVE_MARKERS


class SeedanceClientSafetyError(ValueError):
    """Raised when a request payload would leak credentials or unsafe metadata."""


class SeedanceClientApiError(RuntimeError):
    """Raised when the remote Seedance API returns an unusable response."""


class SeedanceTransport(Protocol):
    def submit(self, request: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        ...

    def poll(self, request: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        ...

    def download(self, request: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        ...


def _contains_sensitive_marker(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in SENSITIVE_MARKERS)
    if isinstance(value, dict):
        return any(_contains_sensitive_marker(key) or _contains_sensitive_marker(item) for key, item in value.items())
    if isinstance(value, list | tuple | set):
        return any(_contains_sensitive_marker(item) for item in value)
    return False


def _assert_safe_payload(payload: Any, *, context: str) -> None:
    if _contains_sensitive_marker(payload):
        raise SeedanceClientSafetyError(f"sensitive string detected in Seedance {context} payload")


def _normalize_status(status: Any) -> str:
    value = str(status or "").lower()
    if value in {"queued", "created", "pending", "submitted"}:
        return "submitted"
    if value in {"running", "processing", "in_progress"}:
        return "running"
    if value in {"success", "succeeded", "completed", "done"}:
        return "succeeded"
    if value in {"fail", "failed", "error", "cancelled", "canceled"}:
        return "failed"
    return "running"


def _walk_values(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)


def _find_first_string(payload: Any, keys: set[str]) -> str | None:
    for key, value in _walk_values(payload):
        if str(key).lower() in keys and isinstance(value, str) and value:
            return value
    return None


def _find_first_int(payload: Any, keys: set[str], default: int) -> int:
    for key, value in _walk_values(payload):
        if str(key).lower() in keys:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return default


def _sanitized_error_text(payload: bytes, *, limit: int = 400) -> str:
    text = payload.decode("utf-8", errors="replace").strip()
    if not text:
        return "empty response body"
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return "remote response contained sensitive-looking text; body omitted"
    return text[:limit]


class MockSeedanceHttpTransport:
    """Deterministic local transport for contract tests; it never performs network I/O."""

    client_name = "mock_http"

    def submit(self, request: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        digest = hashlib.sha256(f"{request.source_job_id}:{request.scene_id}".encode("utf-8")).hexdigest()[:10]
        return SeedanceClientSubmitResponse(
            client="mock_http",
            dry_run=True,
            task_id=f"seedance_mock_http_{request.scene_id}_{digest}",
            scene_id=request.scene_id,
            status="submitted",
            retry_after_seconds=2,
        )

    def poll(self, request: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        return SeedanceClientPollResponse(
            client="mock_http",
            dry_run=True,
            task_id=request.task_id,
            scene_id=request.scene_id,
            status="succeeded",
            progress_percent=100,
        )

    def download(self, request: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        return SeedanceClientDownloadResponse(
            client="mock_http",
            dry_run=True,
            task_id=request.task_id,
            scene_id=request.scene_id,
            status="downloaded",
            output_path=output_path,
        )


class RealSeedanceHttpTransport:
    client_name = "seedance_real"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3",
        model_name: str,
        ratio: str = "9:16",
        resolution: str = "720p",
        timeout_seconds: int = 120,
        urlopen=request.urlopen,
    ) -> None:
        if not api_key:
            raise ValueError("ARK_API_KEY or SEEDANCE_API_KEY is required for real Seedance calls")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.ratio = ratio
        self.resolution = resolution
        self.timeout_seconds = timeout_seconds
        self.urlopen = urlopen
        self._video_url_by_task_id: dict[str, str] = {}

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except error.HTTPError as exc:
            raw_error = exc.read()
            raise SeedanceClientApiError(f"Seedance API HTTP {exc.code}: {_sanitized_error_text(raw_error)}") from exc
        except error.URLError as exc:
            raise SeedanceClientApiError(f"Seedance API request failed: {exc.reason}") from exc
        if not raw:
            return {}
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise SeedanceClientApiError("Seedance API response must be a JSON object")
        return parsed

    def submit(self, request_payload: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        content: list[dict[str, Any]] = [{"type": "text", "text": request_payload.prompt}]
        if request_payload.image_url:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": request_payload.image_url},
                    "role": "first_frame",
                }
            )
        payload: dict[str, Any] = {
            "model": self.model_name,
            "content": content,
            "duration": int(round(request_payload.duration_seconds)),
            "ratio": self.ratio,
            "resolution": self.resolution,
        }
        response = self._request_json("POST", "/contents/generations/tasks", payload)
        task_id = _find_first_string(response, {"id", "task_id", "taskid"})
        if not task_id:
            raise SeedanceClientApiError("Seedance submit response did not contain a task id")
        return SeedanceClientSubmitResponse(
            client="seedance_real",
            dry_run=False,
            task_id=task_id,
            scene_id=request_payload.scene_id,
            status="submitted",
            retry_after_seconds=_find_first_int(response, {"retry_after", "retry_after_seconds"}, 5),
        )

    def poll(self, request_payload: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        response = self._request_json("GET", f"/contents/generations/tasks/{request_payload.task_id}")
        status = _normalize_status(_find_first_string(response, {"status", "state"}))
        progress = _find_first_int(response, {"progress", "progress_percent"}, 100 if status == "succeeded" else 0)
        video_url = _find_first_string(response, {"url", "video_url", "download_url"})
        if video_url and status == "succeeded":
            self._video_url_by_task_id[request_payload.task_id] = video_url
        return SeedanceClientPollResponse(
            client="seedance_real",
            dry_run=False,
            task_id=request_payload.task_id,
            scene_id=request_payload.scene_id,
            status=status,  # type: ignore[arg-type]
            progress_percent=max(0, min(100, progress)),
            error_message=_find_first_string(response, {"message", "error", "reason"}) if status == "failed" else None,
        )

    def download(self, request_payload: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        video_url = self._video_url_by_task_id.get(request_payload.task_id)
        if not video_url:
            raise SeedanceClientApiError("Seedance poll response did not expose a downloadable video URL")
        req = request.Request(video_url, method="GET")
        try:
            with self.urlopen(req, timeout=self.timeout_seconds) as response:
                content = response.read()
        except error.HTTPError as exc:
            raise SeedanceClientApiError(f"Seedance video download HTTP {exc.code}") from exc
        except error.URLError as exc:
            raise SeedanceClientApiError(f"Seedance video download failed: {exc.reason}") from exc
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        return SeedanceClientDownloadResponse(
            client="seedance_real",
            dry_run=False,
            task_id=request_payload.task_id,
            scene_id=request_payload.scene_id,
            status="downloaded",
            output_path=output.as_posix(),
        )


class DisabledSeedanceNetworkTransport:
    """Placeholder for the future real transport; current code must not call it."""

    def submit(self, request: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        raise NotImplementedError("Real Seedance network transport is not implemented; use mock HTTP dry-run")

    def poll(self, request: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        raise NotImplementedError("Real Seedance network transport is not implemented; use mock HTTP dry-run")

    def download(self, request: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        raise NotImplementedError("Real Seedance network transport is not implemented; use mock HTTP dry-run")


class SeedanceApiClient:
    def __init__(self, transport: SeedanceTransport | None = None) -> None:
        self.transport = transport or DisabledSeedanceNetworkTransport()

    def submit(self, request: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        _assert_safe_payload(request.model_dump(mode="json"), context="submit request")
        response = self.transport.submit(request)
        _assert_safe_payload(response.model_dump(mode="json"), context="submit response")
        return response

    def poll(self, request: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        _assert_safe_payload(request.model_dump(mode="json"), context="poll request")
        response = self.transport.poll(request)
        _assert_safe_payload(response.model_dump(mode="json"), context="poll response")
        return response

    def download(self, request: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        _assert_safe_payload(request.model_dump(mode="json"), context="download request")
        response = self.transport.download(request, output_path=output_path)
        _assert_safe_payload(response.model_dump(mode="json"), context="download response")
        return response

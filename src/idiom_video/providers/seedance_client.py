from __future__ import annotations

import hashlib
from typing import Any, Protocol

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


class MockSeedanceHttpTransport:
    """Deterministic local transport for contract tests; it never performs network I/O."""

    client_name = "mock_http"

    def submit(self, request: SeedanceClientSubmitRequest) -> SeedanceClientSubmitResponse:
        digest = hashlib.sha256(f"{request.source_job_id}:{request.scene_id}".encode("utf-8")).hexdigest()[:10]
        return SeedanceClientSubmitResponse(
            task_id=f"seedance_mock_http_{request.scene_id}_{digest}",
            scene_id=request.scene_id,
            status="submitted",
            retry_after_seconds=2,
        )

    def poll(self, request: SeedanceClientPollRequest) -> SeedanceClientPollResponse:
        return SeedanceClientPollResponse(
            task_id=request.task_id,
            scene_id=request.scene_id,
            status="succeeded",
            progress_percent=100,
        )

    def download(self, request: SeedanceClientDownloadRequest, *, output_path: str) -> SeedanceClientDownloadResponse:
        return SeedanceClientDownloadResponse(
            task_id=request.task_id,
            scene_id=request.scene_id,
            status="downloaded",
            output_path=output_path,
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

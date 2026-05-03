from __future__ import annotations

import hashlib
import math
from pathlib import Path

from idiom_video.schemas import CurrencyCode, SeedanceBillingMode, SeedanceCostEstimate, VideoGenerationJob
from idiom_video.utils.json_io import read_json


def video_jobs_fingerprint(video_jobs_path: Path) -> str:
    resolved_path = video_jobs_path.resolve()
    hasher = hashlib.sha256()
    hasher.update(resolved_path.as_posix().encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(resolved_path.read_bytes())
    return f"sha256:{hasher.hexdigest()}"


def _load_video_jobs(story_dir: Path) -> list[VideoGenerationJob]:
    video_jobs_path = story_dir / "05_video_jobs.json"
    return [VideoGenerationJob.model_validate(item) for item in read_json(video_jobs_path)]


def _estimate_tokens(jobs: list[VideoGenerationJob], *, width: int, height: int, fps: int) -> int:
    return sum(math.ceil(job.duration_seconds * width * height * fps / 1024) for job in jobs)


def estimate_seedance_cost(
    story_dir: Path,
    *,
    model_name: str = "Dreamina-Seedance-2.0",
    width: int = 864,
    height: int = 496,
    fps: int = 24,
    currency: CurrencyCode = "USD",
    unit_price_per_million_tokens: float,
    retry_multiplier: float = 1.2,
    billing_mode: SeedanceBillingMode = "input_without_video",
    price_source: str = "manual",
    price_source_url: str | None = None,
    price_checked_at: str | None = None,
) -> SeedanceCostEstimate:
    story_path = story_dir.resolve()
    video_jobs_path = story_path / "05_video_jobs.json"
    jobs = _load_video_jobs(story_path)
    estimated_tokens = _estimate_tokens(jobs, width=width, height=height, fps=fps)
    base_cost = round(estimated_tokens / 1_000_000 * unit_price_per_million_tokens, 4)
    estimated_total_cost = round(base_cost * retry_multiplier, 4)
    total_duration_seconds = round(sum(job.duration_seconds for job in jobs), 3)
    return SeedanceCostEstimate(
        provider="seedance",
        model_name=model_name,
        billing_mode=billing_mode,
        currency=currency,
        unit_price_per_million_tokens=unit_price_per_million_tokens,
        retry_multiplier=retry_multiplier,
        width=width,
        height=height,
        fps=fps,
        clip_count=len(jobs),
        total_duration_seconds=total_duration_seconds,
        estimated_tokens=estimated_tokens,
        base_cost=base_cost,
        estimated_total_cost=estimated_total_cost,
        story_dir=story_path.as_posix(),
        video_jobs_path=video_jobs_path.as_posix(),
        video_jobs_fingerprint=video_jobs_fingerprint(video_jobs_path),
        price_source=price_source,
        price_source_url=price_source_url,
        price_checked_at=price_checked_at,
        notes=[
            "Offline estimate only; this command does not call Seedance or any external service.",
            "Token formula uses duration_seconds * width * height * fps / 1024 per clip.",
            "Actual provider invoices may differ because of model version, endpoint, rounding, retries, or account pricing.",
        ],
    )

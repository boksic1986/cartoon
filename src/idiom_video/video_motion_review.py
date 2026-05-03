from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import (
    ReviewStatus,
    SeedanceDryRunJob,
    Storyboard,
    VideoMotionReview,
    VideoMotionReviewItem,
)
from idiom_video.utils.json_io import read_json


MOTION_REVIEW_CHECKLIST = [
    "首帧图片路径存在，可作为 image-to-video 输入",
    "Seedance dry-run request preview 存在，可人工复查请求内容",
    "运动提示词保留固定背景连续性",
    "动作温和自然，适合儿童向成语动画",
    "镜头时长与分镜和字幕节奏基本匹配",
]

CONTINUITY_MARKERS = ["固定背景连续性", "茅草屋", "田间小径", "树桩"]


def _summary(items: list[VideoMotionReviewItem]) -> dict[str, int]:
    return {
        "approved": sum(1 for item in items if item.status == "approved"),
        "pending": sum(1 for item in items if item.status == "pending"),
        "rejected": sum(1 for item in items if item.status == "rejected"),
    }


def _has_continuity_prompt(prompt: str) -> bool:
    return any(marker in prompt for marker in CONTINUITY_MARKERS)


def _auto_status(image_path: str, request_preview_path: str, continuity_prompt_present: bool, auto: bool) -> ReviewStatus:
    if auto and Path(image_path).exists() and Path(request_preview_path).exists() and continuity_prompt_present:
        return "approved"
    return "pending"


def _load_seedance_dry_run_jobs(story_dir: Path) -> tuple[Path, list[SeedanceDryRunJob]]:
    jobs_path = story_dir / "seedance_dry_run" / "jobs.json"
    if not jobs_path.exists():
        raise FileNotFoundError("seedance_dry_run/jobs.json is required; run generate-videos --provider seedance --dry-run first")
    jobs = [SeedanceDryRunJob.model_validate(item) for item in read_json(jobs_path)]
    if not jobs:
        raise ValueError("seedance_dry_run/jobs.json must contain at least one job")
    return jobs_path, jobs


def build_video_motion_review(story_dir: Path, auto: bool = False) -> VideoMotionReview:
    storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
    jobs_path, jobs = _load_seedance_dry_run_jobs(story_dir)
    jobs_by_scene = {job.scene_id: job for job in jobs}

    items: list[VideoMotionReviewItem] = []
    for scene in storyboard.scenes:
        job = jobs_by_scene.get(scene.scene_id)
        if job is None:
            raise ValueError(f"Seedance dry-run job missing for scene {scene.scene_id}")
        continuity_prompt_present = _has_continuity_prompt(job.prompt)
        status = _auto_status(
            job.image_path,
            job.request_preview_path,
            continuity_prompt_present,
            auto=auto,
        )
        if status == "approved":
            notes = "自动技术检查通过；真实视频生成前仍需人工逐镜确认运动节奏和画面连续性。"
        else:
            notes = "等待人工确认运动提示词、首帧引用和背景连续性；未调用真实视频服务。"
        items.append(
            VideoMotionReviewItem(
                item_id=f"motion_{scene.scene_id}",
                scene_id=scene.scene_id,
                title=f"{scene.title} 运动审核",
                image_path=job.image_path,
                request_preview_path=job.request_preview_path,
                duration_seconds=job.duration_seconds,
                motion_prompt=job.prompt,
                continuity_prompt_present=continuity_prompt_present,
                checklist=MOTION_REVIEW_CHECKLIST,
                status=status,
                notes=notes,
            )
        )

    return VideoMotionReview(
        idiom_slug=storyboard.idiom_slug,
        title=storyboard.title,
        story_dir=story_dir.as_posix(),
        seedance_dry_run_jobs_path=jobs_path.as_posix(),
        auto=auto,
        items=items,
        summary=_summary(items),
    )


def find_video_motion_review_gaps(story_dir: Path, review: VideoMotionReview) -> list[tuple[str, str | None]]:
    gaps: list[tuple[str, str | None]] = []
    jobs_path = story_dir / "seedance_dry_run" / "jobs.json"
    if not jobs_path.exists():
        return [("Seedance dry-run jobs missing for video motion review", jobs_path.as_posix())]

    jobs = [SeedanceDryRunJob.model_validate(item) for item in read_json(jobs_path)]
    job_scene_ids = {job.scene_id for job in jobs}
    items_by_scene = {item.scene_id: item for item in review.items}
    seen_review_scene_ids: set[str] = set()
    for item in review.items:
        if item.scene_id in seen_review_scene_ids:
            gaps.append(("video motion review scene duplicated", f"video_motion_review:{item.item_id}"))
        seen_review_scene_ids.add(item.scene_id)
        if item.scene_id not in job_scene_ids:
            gaps.append(
                (
                    "video motion review scene is not in current Seedance dry-run jobs",
                    f"video_motion_review:{item.item_id}",
                )
            )
    for job in jobs:
        item = items_by_scene.get(job.scene_id)
        if item is None:
            gaps.append(("Seedance dry-run scene missing from video motion review", job.scene_id))
            continue
        if item.image_path != job.image_path:
            gaps.append(("video motion review image path differs from Seedance dry-run job", item.image_path))
        if item.request_preview_path != job.request_preview_path:
            gaps.append(
                (
                    "video motion review request preview differs from Seedance dry-run job",
                    item.request_preview_path,
                )
            )
        if item.motion_prompt != job.prompt:
            gaps.append(("video motion review prompt differs from Seedance dry-run job", f"motion_review:{item.item_id}"))
    return gaps

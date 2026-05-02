from __future__ import annotations

import shutil
from pathlib import Path

import typer

from idiom_video.config import get_settings
from idiom_video.media.cover_generator import generate_cover
from idiom_video.media.ffmpeg_compose import compose_mock_final
from idiom_video.media.metadata_writer import write_publish_metadata
from idiom_video.media.subtitle import storyboard_to_srt
from idiom_video.prompt_builder import build_image_jobs, build_image_prompts
from idiom_video.providers.image_mock import ImageMockProvider
from idiom_video.providers.video_mock import VideoMockProvider
from idiom_video.quality_rules import QualityIssue, QualityResult, check_forbidden_terms, validate_models_manifest
from idiom_video.schemas import (
    IdiomProfile,
    ImageGenerationJob,
    ImagePrompt,
    ReviewItem,
    ReviewRecord,
    Script,
    Storyboard,
    VideoGenerationJob,
)
from idiom_video.script_writer import build_script
from idiom_video.storyboard_writer import build_storyboard
from idiom_video.utils.json_io import read_json, write_json
from idiom_video.utils.logging import info, warn
from idiom_video.utils.paths import output_dir_for_slug, project_root


app = typer.Typer(help="Mock-first pipeline for idiom story short videos.")


def _story_dir_for_profile(profile: IdiomProfile) -> Path:
    settings = get_settings()
    return output_dir_for_slug(settings.output_dir, profile.slug)


def _load_style_text() -> tuple[str, str]:
    root = project_root(Path(__file__).resolve())
    style_path = root / "data" / "style" / "style_bible.md"
    negative_path = root / "data" / "style" / "negative_prompt.md"
    style = style_path.read_text(encoding="utf-8") if style_path.exists() else "原创中国风儿童绘本动画，温暖明亮。"
    negative = negative_path.read_text(encoding="utf-8") if negative_path.exists() else "不要出现品牌 logo、明星脸、复杂文字。"
    return style, negative


def _load_forbidden_terms() -> list[str]:
    root = project_root(Path(__file__).resolve())
    terms_path = root / "data" / "style" / "forbidden_terms.json"
    if not terms_path.exists():
        return ["明星脸", "公众人物", "具体版权角色", "在世艺术家风格", "品牌 logo"]
    data = read_json(terms_path)
    return list(data.get("terms", []))


def _write_prompt_quality_report(story_dir: Path, prompts: list[ImagePrompt]) -> QualityResult:
    forbidden_terms = _load_forbidden_terms()
    issues: list[QualityIssue] = []
    for prompt in prompts:
        result = check_forbidden_terms(prompt.prompt, forbidden_terms)
        for issue in result.issues:
            issues.append(issue.model_copy(update={"path": f"prompt:{prompt.prompt_id}"}))
    quality = QualityResult(ok=not issues, issues=issues)
    write_json(story_dir / "quality_reports" / "prompt_quality.json", quality)
    return quality


def _write_review_record(story_dir: Path, review_type: str, items: list[ReviewItem], auto: bool = True) -> ReviewRecord:
    approved = sum(1 for item in items if item.status == "approved")
    rejected = sum(1 for item in items if item.status == "rejected")
    pending = sum(1 for item in items if item.status == "pending")
    record = ReviewRecord(
        review_type=review_type,
        auto=auto,
        items=items,
        summary={"approved": approved, "rejected": rejected, "pending": pending},
    )
    write_json(story_dir / "review" / f"{review_type}_review.json", record)
    return record


def _quality_issue(message: str, path: str | None = None) -> QualityIssue:
    return QualityIssue(message=message, path=path)


def _run_full_quality_check(story_dir: Path) -> dict:
    issues: list[QualityIssue] = []
    checks: dict[str, str] = {}

    required_files = [
        "01_script.json",
        "02_storyboard.json",
        "03_image_prompts.json",
        "04_image_jobs.json",
        "05_video_jobs.json",
        "subtitles/final.srt",
        "final/metadata.json",
    ]
    missing_required = [name for name in required_files if not (story_dir / name).exists()]
    checks["required_files"] = "failed" if missing_required else "passed"
    for name in missing_required:
        issues.append(_quality_issue("required artifact missing", name))

    prompt_report_path = story_dir / "quality_reports" / "prompt_quality.json"
    if prompt_report_path.exists():
        prompt_report = read_json(prompt_report_path)
        checks["prompt_quality"] = "passed" if prompt_report.get("ok") else "failed"
        for issue in prompt_report.get("issues", []):
            issues.append(QualityIssue.model_validate(issue))
    else:
        checks["prompt_quality"] = "failed"
        issues.append(_quality_issue("prompt quality report missing", "quality_reports/prompt_quality.json"))

    try:
        storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
        checks["storyboard_timing"] = "passed"
        if len(storyboard.scenes) > get_settings().max_scenes:
            checks["storyboard_timing"] = "failed"
            issues.append(_quality_issue("storyboard scene count exceeds limit", "02_storyboard.json"))
    except Exception as exc:
        checks["storyboard_timing"] = "failed"
        issues.append(_quality_issue(f"storyboard validation failed: {exc}", "02_storyboard.json"))

    approved_image_missing = False
    try:
        video_jobs = [VideoGenerationJob.model_validate(item) for item in read_json(story_dir / "05_video_jobs.json")]
        for job in video_jobs:
            if not Path(job.image_path).exists():
                approved_image_missing = True
                issues.append(_quality_issue("approved image missing", job.image_path))
    except Exception as exc:
        approved_image_missing = True
        issues.append(_quality_issue(f"video jobs validation failed: {exc}", "05_video_jobs.json"))
    checks["approved_images"] = "failed" if approved_image_missing else "passed"

    review_failed = False
    review_files = ["review/script_review.json", "review/image_review.json", "review/video_review.json"]
    for name in review_files:
        path = story_dir / name
        if not path.exists():
            review_failed = True
            issues.append(_quality_issue("review record missing", name))
            continue
        try:
            record = ReviewRecord.model_validate(read_json(path))
        except Exception as exc:
            review_failed = True
            issues.append(_quality_issue(f"review record validation failed: {exc}", name))
            continue
        for item in record.items:
            if item.status != "approved":
                review_failed = True
                issues.append(_quality_issue(f"review item is {item.status}", f"{name}:{item.item_id}"))
    checks["review_records"] = "failed" if review_failed else "passed"

    manifest_path = project_root(Path(__file__).resolve()) / "data" / "models" / "models_manifest.json"
    if manifest_path.exists():
        manifest_result = validate_models_manifest(read_json(manifest_path))
        checks["models_manifest"] = "passed" if manifest_result.ok else "failed"
        issues.extend(manifest_result.issues)
    else:
        checks["models_manifest"] = "failed"
        issues.append(_quality_issue("models manifest missing", str(manifest_path)))

    report = {"ok": not issues, "checks": checks, "issues": [issue.model_dump(mode="json") for issue in issues]}
    write_json(story_dir / "quality_reports" / "full_quality.json", report)
    return report


def _write_script(idiom_path: Path) -> Path:
    profile = IdiomProfile.model_validate(read_json(idiom_path))
    story_dir = _story_dir_for_profile(profile)
    script = build_script(profile)
    script_path = write_json(story_dir / "01_script.json", script)
    _write_review_record(
        story_dir,
        "script",
        [ReviewItem(item_id="script", status="approved", notes="mock 流程自动通过，真实生产前需人工复核。")],
    )
    return script_path


def _write_storyboard(script_path: Path) -> Path:
    script = Script.model_validate(read_json(script_path))
    storyboard = build_storyboard(script)
    return write_json(script_path.parent / "02_storyboard.json", storyboard)


def _write_image_prompts(storyboard_path: Path) -> tuple[Path, Path]:
    settings = get_settings()
    storyboard = Storyboard.model_validate(read_json(storyboard_path))
    style, negative = _load_style_text()
    prompts = build_image_prompts(
        storyboard,
        style,
        negative,
        width=settings.default_image_width,
        height=settings.default_image_height,
    )
    quality = _write_prompt_quality_report(storyboard_path.parent, prompts)
    if not quality.ok:
        warn("prompt quality check failed; see quality_reports/prompt_quality.json")
        raise typer.Exit(1)
    jobs = build_image_jobs(prompts, storyboard_path.parent)
    prompts_path = write_json(storyboard_path.parent / "03_image_prompts.json", prompts)
    jobs_path = write_json(storyboard_path.parent / "04_image_jobs.json", jobs)
    return prompts_path, jobs_path


@app.command()
def validate_idiom(idiom_path: Path) -> None:
    profile = IdiomProfile.model_validate(read_json(idiom_path))
    info(f"valid idiom profile: {profile.slug}")


@app.command()
def generate_script(idiom_path: Path) -> None:
    path = _write_script(idiom_path)
    info(f"wrote {path}")


@app.command()
def generate_storyboard(script_path: Path) -> None:
    path = _write_storyboard(script_path)
    info(f"wrote {path}")


def build_image_prompts_command(storyboard_path: Path) -> None:
    prompts_path, jobs_path = _write_image_prompts(storyboard_path)
    info(f"wrote {prompts_path}")
    info(f"wrote {jobs_path}")


app.command(name="build-image-prompts")(build_image_prompts_command)


@app.command()
def generate_images(image_prompts_path: Path, provider: str = typer.Option("mock", "--provider")) -> None:
    if provider != "mock":
        raise typer.BadParameter("first milestone only supports --provider mock")
    prompts = [ImagePrompt.model_validate(item) for item in read_json(image_prompts_path)]
    jobs_path = image_prompts_path.parent / "04_image_jobs.json"
    if jobs_path.exists():
        jobs = [ImageGenerationJob.model_validate(item) for item in read_json(jobs_path)]
    else:
        jobs = build_image_jobs(prompts, image_prompts_path.parent)
        write_json(jobs_path, jobs)
    provider_impl = ImageMockProvider()
    assets = [provider_impl.generate(job) for job in jobs]
    write_json(image_prompts_path.parent / "images_raw" / "assets.json", assets)
    info(f"generated {len(assets)} mock images")


@app.command()
def approve_images(images_raw_dir: Path, auto: bool = typer.Option(False, "--auto")) -> None:
    if not auto:
        raise typer.BadParameter("manual approval UI is deferred; use --auto for the mock milestone")
    story_dir = images_raw_dir.parent
    approved_dir = story_dir / "images_approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
    jobs: list[VideoGenerationJob] = []
    review_items: list[ReviewItem] = []
    for scene in storyboard.scenes:
        raw_path = images_raw_dir / f"{scene.scene_id}.png"
        approved_path = approved_dir / f"{scene.scene_id}.png"
        if not raw_path.exists():
            review_items.append(
                ReviewItem(
                    item_id=f"image_{scene.scene_id}",
                    scene_id=scene.scene_id,
                    asset_path=None,
                    status="pending",
                    notes="未找到对应 raw 图片，等待重新生成或人工处理。",
                )
            )
            continue
        shutil.copy2(raw_path, approved_path)
        jobs.append(
            VideoGenerationJob(
                job_id=f"video_{scene.scene_id}",
                scene_id=scene.scene_id,
                image_path=approved_path.as_posix(),
                prompt=scene.video_prompt_hint,
                duration_seconds=scene.duration_seconds,
                output_path=(story_dir / "videos" / f"{scene.scene_id}.txt").as_posix(),
            )
        )
        review_items.append(
            ReviewItem(
                item_id=f"image_{scene.scene_id}",
                scene_id=scene.scene_id,
                asset_path=approved_path.as_posix(),
                status="approved",
                notes="mock 流程自动审核通过，真实图片需要人工复核。",
            )
        )
    write_json(story_dir / "05_video_jobs.json", jobs)
    _write_review_record(story_dir, "image", review_items)
    info(f"approved images and wrote {len(jobs)} video jobs")


@app.command()
def generate_videos(video_jobs_path: Path, provider: str = typer.Option("mock", "--provider")) -> None:
    if provider != "mock":
        raise typer.BadParameter("first milestone only supports --provider mock")
    jobs = [VideoGenerationJob.model_validate(item) for item in read_json(video_jobs_path)]
    provider_impl = VideoMockProvider()
    clips = [provider_impl.generate(job) for job in jobs]
    write_json(video_jobs_path.parent / "videos" / "clips.json", clips)
    _write_review_record(
        video_jobs_path.parent,
        "video",
        [
            ReviewItem(
                item_id=f"video_{clip.scene_id}",
                scene_id=clip.scene_id,
                clip_path=Path(clip.path).as_posix(),
                status="approved",
                notes="mock 流程自动审核通过，真实视频需要人工复核。",
            )
            for clip in clips
        ],
    )
    info(f"generated {len(clips)} mock video records")


@app.command(name="quality-check")
def quality_check(story_dir: Path) -> None:
    report = _run_full_quality_check(story_dir)
    if not report["ok"]:
        warn("quality check failed; see quality_reports/full_quality.json")
        raise typer.Exit(1)
    info(f"quality check passed: {story_dir / 'quality_reports' / 'full_quality.json'}")


@app.command()
def generate_subtitles(storyboard_path: Path) -> None:
    storyboard = Storyboard.model_validate(read_json(storyboard_path))
    subtitles_dir = storyboard_path.parent / "subtitles"
    subtitles_dir.mkdir(parents=True, exist_ok=True)
    output = subtitles_dir / "final.srt"
    output.write_text(storyboard_to_srt(storyboard), encoding="utf-8")
    info(f"wrote {output}")


@app.command()
def compose(story_dir: Path) -> None:
    result = compose_mock_final(story_dir)
    if not result.used_ffmpeg:
        warn(result.message)
    info(f"wrote {result.output_path}")


@app.command()
def publish_metadata(story_dir: Path) -> None:
    storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
    script = Script.model_validate(read_json(story_dir / "01_script.json"))
    generate_cover(story_dir)
    metadata = write_publish_metadata(story_dir, storyboard, script.moral)
    info(f"wrote metadata for {metadata.idiom_slug}")


@app.command()
def run_all(idiom_path: Path, providers: str = typer.Option("mock", "--providers")) -> None:
    if providers != "mock":
        raise typer.BadParameter("first milestone only supports --providers mock")
    script_path = _write_script(idiom_path)
    storyboard_path = _write_storyboard(script_path)
    prompts_path, _jobs_path = _write_image_prompts(storyboard_path)
    generate_images(prompts_path, provider="mock")
    approve_images(prompts_path.parent / "images_raw", auto=True)
    generate_videos(prompts_path.parent / "05_video_jobs.json", provider="mock")
    generate_subtitles(storyboard_path)
    compose(prompts_path.parent)
    publish_metadata(prompts_path.parent)
    info("mock run-all finished")

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
from idiom_video.schemas import (
    IdiomProfile,
    ImageGenerationJob,
    ImagePrompt,
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


def _write_script(idiom_path: Path) -> Path:
    profile = IdiomProfile.model_validate(read_json(idiom_path))
    story_dir = _story_dir_for_profile(profile)
    script = build_script(profile)
    return write_json(story_dir / "01_script.json", script)


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
    for png in sorted(images_raw_dir.glob("*.png")):
        shutil.copy2(png, approved_dir / png.name)

    storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
    jobs: list[VideoGenerationJob] = []
    for scene in storyboard.scenes:
        jobs.append(
            VideoGenerationJob(
                job_id=f"video_{scene.scene_id}",
                scene_id=scene.scene_id,
                image_path=str(approved_dir / f"{scene.scene_id}.png"),
                prompt=scene.video_prompt_hint,
                duration_seconds=scene.duration_seconds,
                output_path=str(story_dir / "videos" / f"{scene.scene_id}.txt"),
            )
        )
    write_json(story_dir / "05_video_jobs.json", jobs)
    info(f"approved images and wrote {len(jobs)} video jobs")


@app.command()
def generate_videos(video_jobs_path: Path, provider: str = typer.Option("mock", "--provider")) -> None:
    if provider != "mock":
        raise typer.BadParameter("first milestone only supports --provider mock")
    jobs = [VideoGenerationJob.model_validate(item) for item in read_json(video_jobs_path)]
    provider_impl = VideoMockProvider()
    clips = [provider_impl.generate(job) for job in jobs]
    write_json(video_jobs_path.parent / "videos" / "clips.json", clips)
    info(f"generated {len(clips)} mock video records")


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

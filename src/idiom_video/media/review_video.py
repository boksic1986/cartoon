from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from idiom_video.schemas import ReviewVideoManifest, ReviewVideoPlan, ReviewVideoPlanClip, Storyboard, StoryboardScene
from idiom_video.utils.json_io import read_json, write_json


MOTIONS = ("slow_zoom_in", "slow_pan_right", "slow_pan_left", "slow_tilt_up")


def build_review_video_plan(
    story_dir: str | Path,
    *,
    width: int = 720,
    height: int = 1280,
    fps: int = 12,
) -> ReviewVideoPlan:
    story_path = Path(story_dir).resolve()
    storyboard_path = story_path / "02_storyboard.json"
    if not storyboard_path.exists():
        raise FileNotFoundError(f"storyboard not found: {storyboard_path}")

    storyboard = Storyboard.model_validate(read_json(storyboard_path))
    approved_dir = story_path / "images_approved"
    if not approved_dir.exists():
        raise FileNotFoundError(f"approved image directory not found: {approved_dir}")

    clips: list[ReviewVideoPlanClip] = []
    cursor = 0.0
    for index, scene in enumerate(storyboard.scenes):
        image_path = approved_dir / f"{scene.scene_id}.png"
        if not image_path.exists():
            raise FileNotFoundError(f"approved image not found for {scene.scene_id}: {image_path}")
        duration = float(scene.duration_seconds)
        subtitle_text = " ".join(cue.subtitle_text for cue in scene.speech_cues).strip() or scene.title
        clips.append(
            ReviewVideoPlanClip(
                clip_id=f"review_{scene.scene_id}",
                scene_id=scene.scene_id,
                order=scene.order,
                title=scene.title,
                image_path=image_path.as_posix(),
                subtitle_text=subtitle_text,
                duration_seconds=duration,
                start_seconds=round(cursor, 3),
                end_seconds=round(cursor + duration, 3),
                motion=MOTIONS[index % len(MOTIONS)],
            )
        )
        cursor += duration

    final_dir = story_path / "final"
    return ReviewVideoPlan(
        idiom_slug=storyboard.idiom_slug,
        title=storyboard.title,
        story_dir=story_path.as_posix(),
        aspect_ratio=storyboard.aspect_ratio,
        width=width,
        height=height,
        fps=fps,
        clips=clips,
        output_path=(final_dir / "review_v1.mp4").as_posix(),
        fallback_path=(final_dir / "review_v1.gif").as_posix(),
    )


def compose_review_video(
    story_dir: str | Path,
    *,
    width: int = 720,
    height: int = 1280,
    fps: int = 12,
    ffmpeg_path: str | None = None,
    force_fallback: bool = False,
) -> ReviewVideoManifest:
    story_path = Path(story_dir).resolve()
    final_dir = story_path / "final"
    final_dir.mkdir(parents=True, exist_ok=True)

    plan = build_review_video_plan(story_path, width=width, height=height, fps=fps)
    plan_path = write_json(story_path / "09_review_video_plan.json", plan)
    storyboard = Storyboard.model_validate(read_json(story_path / "02_storyboard.json"))

    ffmpeg = None if force_fallback else _find_ffmpeg(ffmpeg_path)
    if ffmpeg:
        try:
            _render_mp4(plan, storyboard, Path(ffmpeg))
            manifest = ReviewVideoManifest(
                ok=True,
                provider="local_ffmpeg",
                plan_path=plan_path.as_posix(),
                output_path=plan.output_path,
                fallback_note_path=None,
                used_ffmpeg=True,
                clip_count=len(plan.clips),
                width=plan.width,
                height=plan.height,
                fps=plan.fps,
                total_duration_seconds=plan.total_duration_seconds,
                message="Created local review MP4 from approved still images and burned-in subtitles.",
            )
            write_json(final_dir / "review_v1_manifest.json", manifest)
            return manifest
        except Exception as exc:
            return _write_gif_fallback(plan, storyboard, plan_path, f"FFmpeg failed: {exc}")

    reason = "FFmpeg was not available." if not force_fallback else "Fallback mode was requested."
    return _write_gif_fallback(plan, storyboard, plan_path, reason)


def _find_ffmpeg(ffmpeg_path: str | None = None) -> str | None:
    if ffmpeg_path:
        candidate = Path(ffmpeg_path)
        if candidate.exists():
            return str(candidate)
        return ffmpeg_path if ffmpeg_path == "ffmpeg" else None

    found = shutil.which("ffmpeg")
    if found:
        return found

    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _render_mp4(plan: ReviewVideoPlan, storyboard: Storyboard, ffmpeg: Path) -> None:
    final_dir = Path(plan.output_path).parent
    frames_dir = final_dir / "review_v1_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for frame in frames_dir.glob("frame_*.jpg"):
        frame.unlink()

    frame_index = 1
    scenes_by_id = {scene.scene_id: scene for scene in storyboard.scenes}
    for clip in plan.clips:
        scene = scenes_by_id[clip.scene_id]
        source = Image.open(clip.image_path)
        frame_count = max(1, int(round(clip.duration_seconds * plan.fps)))
        for local_index in range(frame_count):
            progress = local_index / max(frame_count - 1, 1)
            absolute_second = clip.start_seconds + progress * clip.duration_seconds
            frame = _render_frame(source, scene, clip, plan.width, plan.height, progress, absolute_second)
            frame.save(frames_dir / f"frame_{frame_index:05d}.jpg", quality=88, optimize=True)
            frame_index += 1
        source.close()

    command = [
        str(ffmpeg),
        "-y",
        "-framerate",
        str(plan.fps),
        "-i",
        str(frames_dir / "frame_%05d.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        plan.output_path,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for frame in frames_dir.glob("frame_*.jpg"):
        frame.unlink()
    try:
        frames_dir.rmdir()
    except OSError:
        pass


def _write_gif_fallback(
    plan: ReviewVideoPlan,
    storyboard: Storyboard,
    plan_path: Path,
    reason: str,
) -> ReviewVideoManifest:
    final_dir = Path(plan.fallback_path).parent
    final_dir.mkdir(parents=True, exist_ok=True)
    fallback_path = Path(plan.fallback_path)
    note_path = final_dir / "review_v1_fallback.txt"

    frames: list[Image.Image] = []
    durations: list[int] = []
    scenes_by_id = {scene.scene_id: scene for scene in storyboard.scenes}
    for clip in plan.clips:
        scene = scenes_by_id[clip.scene_id]
        source = Image.open(clip.image_path)
        steps = 3
        for local_index in range(steps):
            progress = local_index / max(steps - 1, 1)
            absolute_second = clip.start_seconds + progress * clip.duration_seconds
            frames.append(
                _render_frame(source, scene, clip, plan.width, plan.height, progress, absolute_second).convert("P")
            )
            durations.append(max(120, int(round(clip.duration_seconds * 1000 / steps))))
        source.close()

    first, rest = frames[0], frames[1:]
    first.save(fallback_path, save_all=True, append_images=rest, duration=durations, loop=0, optimize=True)

    note_path.write_text(
        "\n".join(
            [
                "Local review video fallback.",
                reason,
                f"GIF output: {fallback_path.as_posix()}",
                "Install FFmpeg or the optional imageio-ffmpeg package to create review_v1.mp4.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    manifest = ReviewVideoManifest(
        ok=True,
        provider="pillow_gif_fallback",
        plan_path=plan_path.as_posix(),
        output_path=fallback_path.as_posix(),
        fallback_note_path=note_path.as_posix(),
        used_ffmpeg=False,
        clip_count=len(plan.clips),
        width=plan.width,
        height=plan.height,
        fps=plan.fps,
        total_duration_seconds=plan.total_duration_seconds,
        message=f"{reason} Generated animated GIF fallback for review.",
    )
    write_json(final_dir / "review_v1_manifest.json", manifest)
    return manifest


def _render_frame(
    source: Image.Image,
    scene: StoryboardScene,
    clip: ReviewVideoPlanClip,
    width: int,
    height: int,
    progress: float,
    absolute_second: float,
) -> Image.Image:
    zoom = 1.0 + 0.035 * progress
    frame = _cover_image(source, width, height, zoom=zoom, motion=clip.motion, progress=progress)
    subtitle = _active_subtitle(scene, absolute_second)
    if subtitle:
        _draw_subtitle(frame, subtitle)
    return frame


def _cover_image(source: Image.Image, width: int, height: int, *, zoom: float, motion: str, progress: float) -> Image.Image:
    image = source.convert("RGB")
    scale = max(width / image.width, height / image.height) * zoom
    resized_width = max(width, int(math.ceil(image.width * scale)))
    resized_height = max(height, int(math.ceil(image.height * scale)))
    resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

    max_x = max(0, resized_width - width)
    max_y = max(0, resized_height - height)
    x_ratio = 0.5
    y_ratio = 0.5
    if motion == "slow_pan_right":
        x_ratio = 0.35 + 0.3 * progress
    elif motion == "slow_pan_left":
        x_ratio = 0.65 - 0.3 * progress
    elif motion == "slow_tilt_up":
        y_ratio = 0.62 - 0.24 * progress

    left = int(round(max_x * x_ratio))
    top = int(round(max_y * y_ratio))
    return resized.crop((left, top, left + width, top + height))


def _active_subtitle(scene: StoryboardScene, absolute_second: float) -> str:
    for cue in scene.speech_cues:
        if cue.estimated_start_seconds <= absolute_second <= cue.estimated_end_seconds:
            return cue.subtitle_text
    return scene.speech_cues[0].subtitle_text if scene.speech_cues else ""


def _draw_subtitle(frame: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    margin = max(20, frame.width // 24)
    font_size = max(20, frame.width // 24)
    font = _load_subtitle_font(font_size)
    max_text_width = frame.width - margin * 4
    lines = _wrap_text(text, draw, font, max_text_width, max_lines=3)
    line_height = int(font_size * 1.35)
    box_height = line_height * len(lines) + margin
    left = margin
    right = frame.width - margin
    bottom = frame.height - margin
    top = bottom - box_height
    draw.rounded_rectangle((left, top, right, bottom), radius=12, fill=(20, 24, 28, 176))
    y = top + margin // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        text_width = bbox[2] - bbox[0]
        x = max(left + margin, (frame.width - text_width) // 2)
        draw.text((x, y), line, font=font, fill=(255, 255, 246, 255), stroke_width=2, stroke_fill=(0, 0, 0, 160))
        y += line_height


def _load_subtitle_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/msyhbd.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_text(
    text: str,
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
    *,
    max_lines: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font, stroke_width=2)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
            continue
        lines.append(current)
        current = char
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len("".join(lines)) < len(text):
        lines[-1] = lines[-1].rstrip(".") + "..."
    return lines or [text]

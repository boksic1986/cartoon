from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import PublishMetadata, Storyboard
from idiom_video.utils.json_io import write_json


def write_publish_metadata(story_dir: str | Path, storyboard: Storyboard, moral: str = "") -> PublishMetadata:
    story = Path(story_dir)
    files = {
        "script": "01_script.json",
        "storyboard": "02_storyboard.json",
        "image_prompts": "03_image_prompts.json",
        "image_jobs": "04_image_jobs.json",
        "video_jobs": "05_video_jobs.json",
        "voice_jobs": "06_voice_jobs.json",
        "voice_assets": "audio/voice_assets.json",
        "alignment": "07_alignment.json",
        "lipsync_jobs": "08_lipsync_jobs.json",
        "subtitles": "subtitles/final.srt",
    }
    metadata = PublishMetadata(
        title=f"{storyboard.title}｜成语故事",
        idiom_slug=storyboard.idiom_slug,
        moral=moral,
        duration_seconds=sum(scene.duration_seconds for scene in storyboard.scenes),
        files=files,
        providers={"image": "mock", "video": "mock", "tts": "mock"},
        notes=["Mock metadata for local review. Real publishing is deferred."],
    )
    write_json(story / "final" / "metadata.json", metadata)
    return metadata

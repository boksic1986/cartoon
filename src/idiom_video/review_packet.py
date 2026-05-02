from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import (
    AlignmentCue,
    ComfyUIDryRunJob,
    LipSyncJob,
    ReviewPacket,
    ReviewPacketItem,
    ReviewStatus,
    SeedanceDryRunJob,
    Script,
    Storyboard,
    VideoClip,
    VoiceAsset,
)
from idiom_video.utils.json_io import read_json


SCRIPT_CHECKLIST = ["成语含义准确", "台词短而清楚", "适合儿童和青少年观看"]
IMAGE_CHECKLIST = ["角色形象一致", "服装和时代背景一致", "无品牌标识、公众人物肖像或版权角色"]
VIDEO_CHECKLIST = ["角色身份稳定", "动作温和自然", "镜头时长与旁白和字幕基本匹配"]
VOICE_CHECKLIST = ["配音文本与字幕一致", "情绪标注合理", "无真实 TTS 授权风险"]
LIPSYNC_CHECKLIST = ["当前仅为占位任务", "enabled=false 时不误认为已渲染", "音频和对齐路径可追踪"]


def _status_for_paths(paths: list[str]) -> ReviewStatus:
    return "approved" if all(Path(path).exists() for path in paths) else "pending"


def _summary(items: list[ReviewPacketItem]) -> dict[str, int]:
    return {
        "approved": sum(1 for item in items if item.status == "approved"),
        "pending": sum(1 for item in items if item.status == "pending"),
        "rejected": sum(1 for item in items if item.status == "rejected"),
    }


def _load_list(path: Path, validator):
    if not path.exists():
        return []
    return [validator(item) for item in read_json(path)]


def _packet_item_by_type_scene(packet: ReviewPacket, item_type: str, scene_id: str) -> ReviewPacketItem | None:
    for item in packet.items:
        if item.item_type == item_type and item.scene_id == scene_id:
            return item
    return None


def find_review_packet_dry_run_gaps(story_dir: Path, packet: ReviewPacket) -> list[tuple[str, str | None]]:
    gaps: list[tuple[str, str | None]] = []
    comfyui_dry_run_jobs_path = story_dir / "comfyui_dry_run" / "jobs.json"
    if comfyui_dry_run_jobs_path.exists():
        for job in _load_list(comfyui_dry_run_jobs_path, ComfyUIDryRunJob.model_validate):
            item = _packet_item_by_type_scene(packet, "image", job.scene_id)
            if item is None:
                gaps.append(("ComfyUI dry-run scene missing from review packet", job.scene_id))
                continue
            if comfyui_dry_run_jobs_path.as_posix() not in item.artifact_paths:
                gaps.append(
                    (
                        "ComfyUI dry-run jobs missing from review packet",
                        f"review_packet:{item.item_id}",
                    )
                )
            if job.request_preview_path not in item.artifact_paths:
                gaps.append(
                    (
                        "ComfyUI dry-run request preview missing from review packet",
                        job.request_preview_path,
                    )
                )

    seedance_dry_run_jobs_path = story_dir / "seedance_dry_run" / "jobs.json"
    if seedance_dry_run_jobs_path.exists():
        for job in _load_list(seedance_dry_run_jobs_path, SeedanceDryRunJob.model_validate):
            item = _packet_item_by_type_scene(packet, "video", job.scene_id)
            if item is None:
                gaps.append(("Seedance dry-run scene missing from review packet", job.scene_id))
                continue
            if seedance_dry_run_jobs_path.as_posix() not in item.artifact_paths:
                gaps.append(
                    (
                        "Seedance dry-run jobs missing from review packet",
                        f"review_packet:{item.item_id}",
                    )
                )
            if job.request_preview_path not in item.artifact_paths:
                gaps.append(
                    (
                        "Seedance dry-run request preview missing from review packet",
                        job.request_preview_path,
                    )
                )
    return gaps


def build_review_packet(story_dir: Path) -> ReviewPacket:
    script = Script.model_validate(read_json(story_dir / "01_script.json"))
    storyboard = Storyboard.model_validate(read_json(story_dir / "02_storyboard.json"))
    voice_assets = _load_list(story_dir / "audio" / "voice_assets.json", VoiceAsset.model_validate)
    clips = _load_list(story_dir / "videos" / "clips.json", VideoClip.model_validate)
    alignment = _load_list(story_dir / "07_alignment.json", AlignmentCue.model_validate)
    lipsync_jobs = _load_list(story_dir / "08_lipsync_jobs.json", LipSyncJob.model_validate)
    comfyui_dry_run_jobs_path = story_dir / "comfyui_dry_run" / "jobs.json"
    comfyui_dry_run_jobs = _load_list(comfyui_dry_run_jobs_path, ComfyUIDryRunJob.model_validate)
    seedance_dry_run_jobs_path = story_dir / "seedance_dry_run" / "jobs.json"
    seedance_dry_run_jobs = _load_list(seedance_dry_run_jobs_path, SeedanceDryRunJob.model_validate)

    voice_assets_by_cue = {asset.cue_id: asset for asset in voice_assets}
    clips_by_scene = {clip.scene_id: clip for clip in clips}
    comfyui_dry_run_by_scene = {job.scene_id: job for job in comfyui_dry_run_jobs}
    seedance_dry_run_by_scene = {job.scene_id: job for job in seedance_dry_run_jobs}
    alignment_path = story_dir / "07_alignment.json"

    items: list[ReviewPacketItem] = []
    script_paths = [(story_dir / "01_script.json").as_posix(), (story_dir / "02_storyboard.json").as_posix()]
    items.append(
        ReviewPacketItem(
            item_id="script",
            item_type="script",
            title=f"{script.title} 剧本审核",
            artifact_paths=script_paths,
            checklist=SCRIPT_CHECKLIST,
            status=_status_for_paths(script_paths),
            notes="mock 流程自动整理，真实生产前需人工复核。",
        )
    )

    for scene in storyboard.scenes:
        image_paths = [
            (story_dir / "images_approved" / f"{scene.scene_id}.png").as_posix(),
            (story_dir / "03_image_prompts.json").as_posix(),
        ]
        if comfyui_dry_run_jobs_path.exists():
            image_paths.append(comfyui_dry_run_jobs_path.as_posix())
            comfyui_job = comfyui_dry_run_by_scene.get(scene.scene_id)
            if comfyui_job is not None:
                image_paths.append(comfyui_job.request_preview_path)
        items.append(
            ReviewPacketItem(
                item_id=f"image_{scene.scene_id}",
                item_type="image",
                scene_id=scene.scene_id,
                title=f"{scene.title} 图片审核",
                artifact_paths=image_paths,
                checklist=IMAGE_CHECKLIST,
                status=_status_for_paths(image_paths),
                notes="确认首帧适合后续 image-to-video。",
            )
        )
        clip = clips_by_scene.get(scene.scene_id)
        video_paths = [clip.path if clip else (story_dir / "videos" / f"{scene.scene_id}.txt").as_posix()]
        if seedance_dry_run_jobs_path.exists():
            video_paths.append(seedance_dry_run_jobs_path.as_posix())
            seedance_job = seedance_dry_run_by_scene.get(scene.scene_id)
            if seedance_job is not None:
                video_paths.append(seedance_job.request_preview_path)
        items.append(
            ReviewPacketItem(
                item_id=f"video_{scene.scene_id}",
                item_type="video",
                scene_id=scene.scene_id,
                title=f"{scene.title} 视频审核",
                artifact_paths=video_paths,
                checklist=VIDEO_CHECKLIST,
                status=_status_for_paths(video_paths),
                notes="mock 或 dry-run 结果不代表真实视频已审核。",
            )
        )

    for cue in alignment:
        asset = voice_assets_by_cue.get(cue.cue_id)
        voice_paths = [asset.path if asset else cue.audio_path]
        items.append(
            ReviewPacketItem(
                item_id=f"voice_{cue.cue_id}",
                item_type="voice",
                scene_id=cue.scene_id,
                cue_id=cue.cue_id,
                title=f"{cue.cue_id} 配音审核",
                artifact_paths=voice_paths,
                checklist=VOICE_CHECKLIST,
                status=_status_for_paths(voice_paths),
                notes="当前为 mock 文本音频资产。",
            )
        )

    for job in lipsync_jobs:
        lipsync_paths = [job.output_path, alignment_path.as_posix()]
        items.append(
            ReviewPacketItem(
                item_id=f"lipsync_{job.cue_id}",
                item_type="lipsync",
                scene_id=job.scene_id,
                cue_id=job.cue_id,
                title=f"{job.cue_id} 口型任务审核",
                artifact_paths=lipsync_paths,
                checklist=LIPSYNC_CHECKLIST,
                status=_status_for_paths(lipsync_paths),
                notes=job.reason,
            )
        )

    return ReviewPacket(
        idiom_slug=storyboard.idiom_slug,
        title=storyboard.title,
        story_dir=story_dir.as_posix(),
        items=items,
        summary=_summary(items),
    )

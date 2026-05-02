from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import AlignmentCue, AlignmentToken, LipSyncJob, Storyboard, VoiceJob


def build_voice_jobs(storyboard: Storyboard, story_dir: str | Path) -> list[VoiceJob]:
    base_dir = Path(story_dir)
    jobs: list[VoiceJob] = []
    for scene in storyboard.scenes:
        for cue in scene.speech_cues:
            jobs.append(
                VoiceJob(
                    job_id=f"voice_{cue.cue_id}",
                    cue_id=cue.cue_id,
                    scene_id=cue.scene_id,
                    speaker_id=cue.speaker_id,
                    speaker_name=cue.speaker_name,
                    text=cue.voice_text,
                    emotion=cue.emotion,
                    start_seconds=cue.estimated_start_seconds,
                    end_seconds=cue.estimated_end_seconds,
                    output_path=(base_dir / "audio" / f"{cue.cue_id}.txt").as_posix(),
                )
            )
    return jobs


def build_alignment(storyboard: Storyboard, voice_jobs: list[VoiceJob]) -> list[AlignmentCue]:
    expected_cue_ids = [cue.cue_id for scene in storyboard.scenes for cue in scene.speech_cues]
    jobs_by_cue_id: dict[str, VoiceJob] = {}
    for job in voice_jobs:
        if job.cue_id in jobs_by_cue_id:
            raise ValueError(f"duplicate voice job for cue: {job.cue_id}")
        jobs_by_cue_id[job.cue_id] = job
    missing_cue_ids = [cue_id for cue_id in expected_cue_ids if cue_id not in jobs_by_cue_id]
    if missing_cue_ids:
        raise ValueError(f"missing voice job for cue: {missing_cue_ids[0]}")
    unexpected_cue_ids = [cue_id for cue_id in jobs_by_cue_id if cue_id not in expected_cue_ids]
    if unexpected_cue_ids:
        raise ValueError(f"unexpected voice job for cue: {unexpected_cue_ids[0]}")
    alignment: list[AlignmentCue] = []
    for scene in storyboard.scenes:
        for cue in scene.speech_cues:
            job = jobs_by_cue_id[cue.cue_id]
            alignment.append(
                AlignmentCue(
                    cue_id=cue.cue_id,
                    scene_id=cue.scene_id,
                    speaker_id=cue.speaker_id,
                    text=cue.voice_text,
                    audio_path=job.output_path,
                    start_seconds=cue.estimated_start_seconds,
                    end_seconds=cue.estimated_end_seconds,
                    tokens=[
                        AlignmentToken(
                            index=1,
                            text=cue.voice_text,
                            start_seconds=cue.estimated_start_seconds,
                            end_seconds=cue.estimated_end_seconds,
                        )
                    ],
                )
            )
    return alignment


def build_lipsync_jobs(alignment: list[AlignmentCue], story_dir: str | Path) -> list[LipSyncJob]:
    base_dir = Path(story_dir)
    alignment_path = (base_dir / "07_alignment.json").as_posix()
    return [
        LipSyncJob(
            job_id=f"lipsync_{cue.cue_id}",
            cue_id=cue.cue_id,
            scene_id=cue.scene_id,
            audio_path=cue.audio_path,
            alignment_path=alignment_path,
            enabled=False,
            reason="MVP 阶段只记录口型任务，暂不做精确口型同步。",
            output_path=(base_dir / "lipsync" / f"{cue.cue_id}.txt").as_posix(),
        )
        for cue in alignment
    ]

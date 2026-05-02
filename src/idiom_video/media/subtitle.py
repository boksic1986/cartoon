from __future__ import annotations

from idiom_video.schemas import Storyboard


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def storyboard_to_srt(storyboard: Storyboard) -> str:
    blocks: list[str] = []
    index = 1
    for scene in storyboard.scenes:
        for cue in scene.speech_cues:
            blocks.append(
                "\n".join(
                    [
                        str(index),
                        f"{format_srt_time(cue.estimated_start_seconds)} --> {format_srt_time(cue.estimated_end_seconds)}",
                        cue.subtitle_text,
                    ]
                )
            )
            index += 1
    return "\n\n".join(blocks) + "\n"

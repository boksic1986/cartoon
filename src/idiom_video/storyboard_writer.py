from __future__ import annotations

from idiom_video.schemas import Script, SpeechCue, Storyboard, StoryboardScene


CAMERAS = {
    "scene_01": "中景，竖屏构图，角色位于画面中心偏下",
    "scene_02": "中近景，树桩在画面一侧，动作清楚但温和",
    "scene_03": "半身镜头，阿木看着树桩思考",
    "scene_04": "固定镜头，阿木坐在树桩旁等待",
    "scene_05": "稍远景，田地和阿木一起入画",
    "scene_06": "明亮中景，阿木重新拿起农具",
}

ACTIONS = {
    "scene_01": "阿木缓慢锄地，阳光柔和。",
    "scene_02": "小兔从小路跑来，停在树桩旁，阿木惊讶弯腰查看。",
    "scene_03": "阿木抱着农具想象好运，表情天真又犹豫。",
    "scene_04": "阿木坐在树桩旁东张西望，田里的农具放在一边。",
    "scene_05": "阿木望着荒掉的田地发愁，风吹过稀疏庄稼。",
    "scene_06": "阿木重新锄地，神情认真，画面温暖明亮。",
}


def _retime_cues(cues: list[SpeechCue], scene_start: float, scene_duration: float) -> list[SpeechCue]:
    if not cues:
        return []
    segment = scene_duration / len(cues)
    timed: list[SpeechCue] = []
    for index, cue in enumerate(cues):
        start = scene_start + segment * index
        end = scene_start + segment * (index + 1)
        timed.append(
            cue.model_copy(
                update={
                    "estimated_start_seconds": round(start, 3),
                    "estimated_end_seconds": round(end, 3),
                }
            )
        )
    return timed


def build_storyboard(script: Script) -> Storyboard:
    scenes: list[StoryboardScene] = []
    current_time = 0.0
    for scene in script.scenes:
        cues = _retime_cues(scene.speech_cues, current_time, scene.duration_seconds)
        scenes.append(
            StoryboardScene(
                scene_id=scene.scene_id,
                order=scene.order,
                title=scene.title,
                visual_description=scene.visual_goal,
                camera=CAMERAS.get(scene.scene_id, "竖屏中景，画面稳定"),
                action=ACTIONS.get(scene.scene_id, scene.summary),
                duration_seconds=scene.duration_seconds,
                image_prompt_hint=f"{scene.title}，{scene.visual_goal}",
                video_prompt_hint=f"保持角色、服装和古代场景一致。{ACTIONS.get(scene.scene_id, scene.summary)}",
                speech_cues=cues,
            )
        )
        current_time += scene.duration_seconds
    return Storyboard(idiom_slug=script.idiom_slug, title=script.title, scenes=scenes)

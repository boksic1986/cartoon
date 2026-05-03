from __future__ import annotations

from idiom_video.schemas import Script, SpeechCue, Storyboard, StoryboardScene


CAMERAS = {
    "scene_01": "中景，竖屏构图，角色位于画面中心偏下",
    "scene_02": "稍远景，小路从画面右侧斜向左前方的树桩，兔子运动方向清楚",
    "scene_03": "中近景，树桩在画面左侧，兔子躺在树桩旁，阿木弯腰查看",
    "scene_04": "半身镜头，阿木看着树桩认真思考",
    "scene_05": "想象感中景，阿木在前景憨厚幻想",
    "scene_06": "固定中景，春末清晨，阿木坐在树桩旁等待，树桩和田垄一起入画",
    "scene_07": "低角度中近景，初夏午后，阿木趴在草席上靠近树桩，小虫和落叶在前景",
    "scene_08": "稍远景，夏末傍晚，田地、树桩和正在打盹的阿木一起入画",
    "scene_09": "半身中景，初秋清晨，阿木从草席上坐起身，树桩、落叶和逐渐荒掉的田地入画",
    "scene_10": "初秋傍晚的明亮中景，阿木站在已整理过的田垄旁重新拿起农具，构图要明显区别于第一镜",
}

ACTIONS = {
    "scene_01": "阿木缓慢锄地，阳光柔和。",
    "scene_02": "小兔从右侧小路朝树桩方向跑向树桩，带起一点尘土，阿木还在远处干活。",
    "scene_03": "小兔撞到树桩后安全地躺在地上，头晕小星星围着耳朵转，无血迹、无伤口；阿木惊讶弯腰查看。",
    "scene_04": "阿木扶着锄头看树桩，眼睛亮起来，像在认真研究一件大事。",
    "scene_05": "阿木幻想几只小兔乖乖排队来到树桩旁，他抱着篮子笑得很憨。",
    "scene_06": "春末，阿木搬来小板凳坐在树桩旁空手托腮等待，只带水壶和小包袱；田垄仍然整齐，作物正常翠绿，大树树叶浓绿，远山清亮蓝绿。",
    "scene_07": "初夏，田边刚出现少量杂草；阿木趴在草席上空手看小虫爬过树桩旁，忽然把一片落叶误看成兔子；大树树叶仍浓绿，远山青绿。",
    "scene_08": "夏末，又过了些日子，作物叶尖发黄、田里杂草变多但没有完全枯死；阿木空手躺在树荫下打盹，草帽盖在脸上，树冠开始泛黄，远山带一点暖黄色薄雾。",
    "scene_09": "初秋，更久以后，更多杂草长出，部分作物低垂；阿木从草席上坐起身，空手看着落叶和荒掉的田地，终于明白自己想错了；大树有少量黄叶飘落，远山偏灰蓝。",
    "scene_10": "初秋傍晚，结尾镜头要明显区别于第一镜：阿木先收起小板凳和草席，把它们放到茅草屋旁，再站到田垄侧面重新锄地；画面里保留树桩但不把它当主角，田里有一小片重新整理好的整齐土垄和新发绿苗，作物状态从荒芜转向恢复，树叶带少量金黄，远山偏暖灰蓝，阿木神情认真又轻松。",
}

BACKGROUND_CONTINUITY = (
    "固定背景连续性：同一座茅草屋始终位于画面右后方靠山脚，屋前木栅栏和水缸保持一致；"
    "田间小径始终从画面右下角弯向右后方茅草屋，经过树桩右侧；"
    "树桩位置、田垄方向和远山轮廓保持一致。"
)


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
        action = ACTIONS.get(scene.scene_id, scene.summary)
        visual_goal = scene.visual_goal.rstrip("。.!！？?")
        scenes.append(
            StoryboardScene(
                scene_id=scene.scene_id,
                order=scene.order,
                title=scene.title,
                visual_description=scene.visual_goal,
                camera=CAMERAS.get(scene.scene_id, "竖屏中景，画面稳定"),
                action=action,
                duration_seconds=scene.duration_seconds,
                image_prompt_hint=f"{scene.title}，{visual_goal}。{BACKGROUND_CONTINUITY}画面动作：{action}",
                video_prompt_hint=f"保持角色、服装和古代场景一致。{BACKGROUND_CONTINUITY}{action}",
                speech_cues=cues,
            )
        )
        current_time += scene.duration_seconds
    return Storyboard(idiom_slug=script.idiom_slug, title=script.title, scenes=scenes)

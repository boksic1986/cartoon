from __future__ import annotations

from idiom_video.schemas import IdiomProfile, Script, ScriptScene, SpeechCue


def _cue(
    cue_id: str,
    scene_id: str,
    speaker_id: str,
    speaker_name: str,
    kind: str,
    text: str,
    emotion: str,
    mouth_action: str,
    duration: float,
) -> SpeechCue:
    return SpeechCue(
        cue_id=cue_id,
        scene_id=scene_id,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        kind=kind,
        voice_text=text,
        subtitle_text=text,
        emotion=emotion,
        mouth_action=mouth_action,
        lip_sync_required=False,
        estimated_start_seconds=0.0,
        estimated_end_seconds=duration,
    )


def build_script(profile: IdiomProfile) -> Script:
    farmer = next((char for char in profile.characters if char.id == "farmer_amu"), profile.characters[0])
    scenes = [
        ScriptScene(
            scene_id="scene_01",
            order=1,
            title="清晨耕田",
            summary="阿木每天在田里认真干活。",
            visual_goal="建立古代农田、树桩和主角形象。",
            duration_seconds=5.0,
            speech_cues=[
                _cue(
                    "scene_01_narration",
                    "scene_01",
                    "narrator",
                    "旁白",
                    "narration",
                    "很久以前，有个农夫叫阿木，每天都认真在田里干活。",
                    "warm",
                    "none",
                    5.0,
                )
            ],
        ),
        ScriptScene(
            scene_id="scene_02",
            order=2,
            title="兔子撞树",
            summary="一只兔子意外撞到树桩，阿木捡到了兔子。",
            visual_goal="表现偶然事件，不夸张不血腥。",
            duration_seconds=6.0,
            speech_cues=[
                _cue(
                    "scene_02_narration",
                    "scene_02",
                    "narrator",
                    "旁白",
                    "narration",
                    "忽然，一只小兔跑得太急，撞到田边的树桩旁。",
                    "surprised",
                    "none",
                    3.0,
                ),
                _cue(
                    "scene_02_dialogue",
                    "scene_02",
                    farmer.id,
                    farmer.name,
                    "dialogue",
                    "咦？今天的好运气可真突然！",
                    "surprised",
                    "speaking_simple",
                    3.0,
                ),
            ],
        ),
        ScriptScene(
            scene_id="scene_03",
            order=3,
            title="心生侥幸",
            summary="阿木觉得以后也许不用干活。",
            visual_goal="让观众看出阿木把偶然当成方法。",
            duration_seconds=6.0,
            speech_cues=[
                _cue(
                    "scene_03_dialogue",
                    "scene_03",
                    farmer.id,
                    farmer.name,
                    "dialogue",
                    "要是每天都有兔子来，我是不是就不用这么辛苦了？",
                    "hopeful",
                    "speaking_simple",
                    6.0,
                )
            ],
        ),
        ScriptScene(
            scene_id="scene_04",
            order=4,
            title="守着树桩",
            summary="阿木放下农具，整天坐在树桩旁等待。",
            visual_goal="表现等待和田地被忽略。",
            duration_seconds=7.0,
            speech_cues=[
                _cue(
                    "scene_04_narration",
                    "scene_04",
                    "narrator",
                    "旁白",
                    "narration",
                    "从那天起，阿木不再认真耕田，只守着树桩等兔子。",
                    "concerned",
                    "none",
                    7.0,
                )
            ],
        ),
        ScriptScene(
            scene_id="scene_05",
            order=5,
            title="田地荒了",
            summary="兔子没有再来，田里的庄稼也越来越差。",
            visual_goal="温和展示错误选择的结果。",
            duration_seconds=7.0,
            speech_cues=[
                _cue(
                    "scene_05_dialogue",
                    "scene_05",
                    farmer.id,
                    farmer.name,
                    "dialogue",
                    "怎么还没有兔子来呢？我的田也快荒了。",
                    "worried",
                    "speaking_simple",
                    7.0,
                )
            ],
        ),
        ScriptScene(
            scene_id="scene_06",
            order=6,
            title="明白道理",
            summary="阿木重新拿起农具，明白不能靠等待生活。",
            visual_goal="给出积极结尾和成语寓意。",
            duration_seconds=6.0,
            speech_cues=[
                _cue(
                    "scene_06_narration",
                    "scene_06",
                    "narrator",
                    "旁白",
                    "narration",
                    f"这就是{profile.idiom}。偶然的好运不能代替勤劳和思考。",
                    "clear",
                    "none",
                    6.0,
                )
            ],
        ),
    ]
    return Script(
        idiom_slug=profile.slug,
        title=profile.idiom,
        moral=profile.moral,
        characters=profile.characters,
        scenes=scenes,
    )

from __future__ import annotations

from pathlib import PureWindowsPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SpeechKind = Literal["narration", "dialogue"]
MouthAction = Literal["none", "speaking_simple", "reaction"]


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CharacterProfile(StrictSchemaModel):
    id: str
    name: str
    role: str
    visual_description: str
    voice_description: str


class SceneProfile(StrictSchemaModel):
    id: str
    location: str
    era: str
    description: str


class IdiomProfile(StrictSchemaModel):
    idiom: str
    pinyin: str
    slug: str
    literal_meaning: str
    moral: str
    source_note: str = ""
    age_range: str = "8-14"
    characters: list[CharacterProfile]
    scenes: list[SceneProfile]
    tags: list[str] = Field(default_factory=list)

    @field_validator("characters", "scenes")
    @classmethod
    def require_non_empty(cls, value: list[object]) -> list[object]:
        if not value:
            raise ValueError("must contain at least one item")
        return value


class SpeechCue(StrictSchemaModel):
    cue_id: str
    scene_id: str
    speaker_id: str
    speaker_name: str
    kind: SpeechKind
    voice_text: str
    subtitle_text: str
    emotion: str = "neutral"
    mouth_action: MouthAction = "none"
    lip_sync_required: bool = False
    estimated_start_seconds: float = Field(ge=0)
    estimated_end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timing(self) -> SpeechCue:
        if self.estimated_end_seconds <= self.estimated_start_seconds:
            raise ValueError("speech cue end time must be after start time")
        return self


class ScriptScene(StrictSchemaModel):
    scene_id: str
    order: int = Field(ge=1)
    title: str
    summary: str
    visual_goal: str
    duration_seconds: float = Field(gt=0, le=10)
    speech_cues: list[SpeechCue]


class Script(StrictSchemaModel):
    idiom_slug: str
    title: str
    moral: str
    characters: list[CharacterProfile]
    scenes: list[ScriptScene]

    @model_validator(mode="after")
    def validate_scene_limits(self) -> Script:
        if len(self.scenes) > 10:
            raise ValueError("script cannot exceed 10 scenes")
        if sum(scene.duration_seconds for scene in self.scenes) > 60:
            raise ValueError("script cannot exceed 60 seconds")
        return self


class StoryboardScene(StrictSchemaModel):
    scene_id: str
    order: int = Field(ge=1)
    title: str
    visual_description: str
    camera: str
    action: str
    duration_seconds: float = Field(gt=0)
    image_prompt_hint: str
    video_prompt_hint: str
    speech_cues: list[SpeechCue]


class Storyboard(StrictSchemaModel):
    idiom_slug: str
    title: str
    aspect_ratio: str = "9:16"
    scenes: list[StoryboardScene]

    @field_validator("scenes")
    @classmethod
    def require_scenes(cls, value: list[StoryboardScene]) -> list[StoryboardScene]:
        if not value:
            raise ValueError("storyboard must contain scenes")
        if len(value) > 10:
            raise ValueError("storyboard cannot exceed 10 scenes")
        return value

    @model_validator(mode="after")
    def validate_total_duration(self) -> Storyboard:
        if sum(scene.duration_seconds for scene in self.scenes) > 60:
            raise ValueError("storyboard cannot exceed 60 seconds")
        return self


class ImagePrompt(StrictSchemaModel):
    prompt_id: str
    scene_id: str
    prompt: str
    negative_prompt: str
    seed: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ImageGenerationJob(StrictSchemaModel):
    job_id: str
    scene_id: str
    prompt: str
    negative_prompt: str
    output_path: str
    seed: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    provider: str = "mock"

    @field_validator("output_path")
    @classmethod
    def accept_windows_paths(cls, value: str) -> str:
        PureWindowsPath(value)
        return value


class ImageAsset(StrictSchemaModel):
    asset_id: str
    scene_id: str
    path: str
    metadata_path: str
    provider: str = "mock"
    seed: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class VideoGenerationJob(StrictSchemaModel):
    job_id: str
    scene_id: str
    image_path: str
    prompt: str
    duration_seconds: float = Field(gt=0, le=10)
    output_path: str
    provider: str = "mock"


class VideoClip(StrictSchemaModel):
    clip_id: str
    scene_id: str
    path: str
    duration_seconds: float = Field(gt=0)
    provider: str = "mock"


class SubtitleCue(StrictSchemaModel):
    index: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str


class PublishMetadata(StrictSchemaModel):
    title: str
    idiom_slug: str
    moral: str
    duration_seconds: float = Field(ge=0)
    files: dict[str, str]
    providers: dict[str, str]
    notes: list[str] = Field(default_factory=list)


ReviewType = Literal["script", "image", "video"]
ReviewStatus = Literal["approved", "rejected", "pending"]


class ReviewItem(StrictSchemaModel):
    item_id: str
    status: ReviewStatus
    scene_id: str | None = None
    asset_path: str | None = None
    clip_path: str | None = None
    notes: str = ""


class ReviewRecord(StrictSchemaModel):
    review_type: ReviewType
    auto: bool = False
    items: list[ReviewItem]
    summary: dict[str, int]

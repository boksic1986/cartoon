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


class ComfyUIDryRunJob(StrictSchemaModel):
    dry_run_id: str
    source_job_id: str
    scene_id: str
    workflow_path: str
    prompt: str
    negative_prompt: str
    seed: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    intended_output_path: str
    request_preview_path: str
    provider: str = "comfyui"
    dry_run: bool = True


class ModelManifestEntry(StrictSchemaModel):
    name: str
    type: str
    local_path: str
    source: str
    license: str
    commercial_use_allowed: bool | None
    notes: str = ""

    @field_validator("name", "type", "local_path", "source", "license")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class ModelManifest(StrictSchemaModel):
    models: list[ModelManifestEntry]

    @field_validator("models")
    @classmethod
    def require_models(cls, value: list[ModelManifestEntry]) -> list[ModelManifestEntry]:
        if not value:
            raise ValueError("models manifest must contain at least one model")
        return value


class ComfyUISmokeCheckIssue(StrictSchemaModel):
    message: str
    path: str | None = None


class ComfyUISmokeCheckReport(StrictSchemaModel):
    ok: bool
    workflow_path: str
    manifest_path: str
    dry_run_jobs_path: str
    checks: dict[str, str]
    issues: list[ComfyUISmokeCheckIssue] = Field(default_factory=list)


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


class SeedanceDryRunJob(StrictSchemaModel):
    dry_run_id: str
    source_job_id: str
    scene_id: str
    image_path: str
    prompt: str
    duration_seconds: float = Field(gt=0, le=10)
    intended_output_path: str
    request_preview_path: str
    provider: str = "seedance"
    dry_run: bool = True


class VoiceJob(StrictSchemaModel):
    job_id: str
    cue_id: str
    scene_id: str
    speaker_id: str
    speaker_name: str
    text: str
    emotion: str = "neutral"
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    output_path: str
    provider: str = "mock"

    @model_validator(mode="after")
    def validate_timing(self) -> VoiceJob:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("voice job end time must be after start time")
        return self


class VoiceAsset(StrictSchemaModel):
    asset_id: str
    cue_id: str
    scene_id: str
    path: str
    metadata_path: str
    duration_seconds: float = Field(gt=0)
    provider: str = "mock"


class AlignmentToken(StrictSchemaModel):
    index: int = Field(ge=1)
    text: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timing(self) -> AlignmentToken:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("alignment token end time must be after start time")
        return self


class AlignmentCue(StrictSchemaModel):
    cue_id: str
    scene_id: str
    speaker_id: str
    text: str
    audio_path: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    tokens: list[AlignmentToken]
    provider: str = "mock"

    @model_validator(mode="after")
    def validate_timing(self) -> AlignmentCue:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("alignment cue end time must be after start time")
        return self

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


class LipSyncJob(StrictSchemaModel):
    job_id: str
    cue_id: str
    scene_id: str
    audio_path: str
    alignment_path: str
    enabled: bool = False
    reason: str
    output_path: str
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
ReviewPacketItemType = Literal["script", "image", "video", "voice", "lipsync", "metadata"]


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


class ReviewPacketItem(StrictSchemaModel):
    item_id: str
    item_type: ReviewPacketItemType
    title: str
    artifact_paths: list[str]
    checklist: list[str]
    status: ReviewStatus = "pending"
    scene_id: str | None = None
    cue_id: str | None = None
    notes: str = ""

    @field_validator("artifact_paths", "checklist")
    @classmethod
    def require_non_empty_list(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("must contain at least one item")
        return value


class ReviewPacket(StrictSchemaModel):
    idiom_slug: str
    title: str
    story_dir: str
    items: list[ReviewPacketItem]
    summary: dict[str, int]

    @field_validator("items")
    @classmethod
    def require_items(cls, value: list[ReviewPacketItem]) -> list[ReviewPacketItem]:
        if not value:
            raise ValueError("review packet must contain items")
        return value

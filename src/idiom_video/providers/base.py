from __future__ import annotations

from typing import Protocol

from idiom_video.schemas import ImageAsset, ImageGenerationJob, VideoClip, VideoGenerationJob


class ImageProvider(Protocol):
    def generate(self, job: ImageGenerationJob) -> ImageAsset:
        ...


class VideoProvider(Protocol):
    def generate(self, job: VideoGenerationJob) -> VideoClip:
        ...


class VoiceProvider(Protocol):
    def synthesize(self, text: str, output_path: str) -> str:
        ...

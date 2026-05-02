from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    image_provider: str = "mock"
    video_provider: str = "mock"
    tts_provider: str = "mock"
    output_dir: Path = Field(default=Path("outputs"))
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_workflow_dir: Path = Path("workflows/comfyui")
    default_aspect_ratio: str = "9:16"
    default_width: int = 1080
    default_height: int = 1920
    default_image_width: int = 768
    default_image_height: int = 1344
    default_duration_seconds: int = 45
    max_scenes: int = 10
    max_video_seconds: int = 60


def get_settings() -> Settings:
    return Settings()

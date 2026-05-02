from __future__ import annotations

from pathlib import Path

from idiom_video.schemas import ImageGenerationJob, ImagePrompt, Storyboard


def build_image_prompts(
    storyboard: Storyboard,
    style_text: str,
    negative_text: str,
    width: int = 768,
    height: int = 1344,
    seed_start: int = 20260502,
) -> list[ImagePrompt]:
    prompts: list[ImagePrompt] = []
    clean_style = style_text.strip()
    clean_negative = negative_text.strip()
    for index, scene in enumerate(storyboard.scenes):
        prompt = "\n".join(
            [
                clean_style,
                f"成语故事《{storyboard.title}》分镜 {scene.order}：{scene.title}。",
                scene.visual_description,
                scene.camera,
                scene.action,
                scene.image_prompt_hint,
                "竖屏 9:16，适合儿童教育短视频，画面不要出现复杂中文文字。",
            ]
        )
        prompts.append(
            ImagePrompt(
                prompt_id=f"prompt_{scene.scene_id}",
                scene_id=scene.scene_id,
                prompt=prompt,
                negative_prompt=clean_negative,
                seed=seed_start + index,
                width=width,
                height=height,
            )
        )
    return prompts


def build_image_jobs(prompts: list[ImagePrompt], story_dir: str | Path) -> list[ImageGenerationJob]:
    base = Path(story_dir)
    return [
        ImageGenerationJob(
            job_id=f"image_{prompt.scene_id}",
            scene_id=prompt.scene_id,
            prompt=prompt.prompt,
            negative_prompt=prompt.negative_prompt,
            output_path=(base / "images_raw" / f"{prompt.scene_id}.png").as_posix(),
            seed=prompt.seed,
            width=prompt.width,
            height=prompt.height,
        )
        for prompt in prompts
    ]

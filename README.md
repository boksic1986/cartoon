# Idiom Video Studio

Mock-first engineering pipeline for producing Chinese idiom story short videos.
The first milestone runs fully offline: no real image API, video API, TTS API,
ComfyUI server, or API key is required.

## Install With Conda

```powershell
cd D:\pipeline\cartoon\idiom-video-studio
& D:\ProgramData\miniconda3\Scripts\conda.exe env create -f environment.yml
```

If the environment already exists:

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pip install -e ".[dev]"
```

The recommended Windows commands avoid relying on shell activation. If you want
interactive activation in PowerShell, initialize conda first and then run
`conda activate idiom-video`.

## China Mirror Configuration

The local development machine can use stable domestic mirrors:

```powershell
# pip, currently configured on this machine
D:\ProgramData\miniconda3\python.exe -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
D:\ProgramData\miniconda3\python.exe -m pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
```

Conda is configured through `C:\Users\11217\.condarc` to use Tsinghua mirrors
for defaults, conda-forge, pytorch, and nvidia channels. Aliyun PyPI can be used
as a fallback by changing the pip index to `https://mirrors.aliyun.com/pypi/simple/`.

## Run The Mock Pipeline

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data/idioms/shou-zhu-dai-tu.json --providers mock
```

The output appears in:

```txt
outputs/shou-zhu-dai-tu/
```

Expected files include:

```txt
01_script.json
02_storyboard.json
03_image_prompts.json
04_image_jobs.json
05_video_jobs.json
quality_reports/prompt_quality.json
subtitles/final.srt
final/metadata.json
final/final_mock.mp4 or final/final_mock.txt
```

## Single-Step Commands

```powershell
idiom-video validate-idiom data/idioms/shou-zhu-dai-tu.json
idiom-video generate-script data/idioms/shou-zhu-dai-tu.json
idiom-video generate-storyboard outputs/shou-zhu-dai-tu/01_script.json
idiom-video build-image-prompts outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video generate-images outputs/shou-zhu-dai-tu/03_image_prompts.json --provider mock
idiom-video approve-images outputs/shou-zhu-dai-tu/images_raw --auto
idiom-video generate-videos outputs/shou-zhu-dai-tu/05_video_jobs.json --provider mock
idiom-video generate-subtitles outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video compose outputs/shou-zhu-dai-tu/
idiom-video publish-metadata outputs/shou-zhu-dai-tu/
```

`build-image-prompts` writes `quality_reports/prompt_quality.json`. The first
milestone checks positive image prompts for forbidden terms and stops before
image generation if a prompt needs human review. Negative prompts can contain
blocked concepts because they are explicit exclusions.

## Dialogue, Voice, And Lip Sync

Dialogue text is created in `01_script.json`. `02_storyboard.json` assigns each
narration or dialogue line to scenes through structured speech cues. The first
milestone records `speaker_id`, `voice_text`, `subtitle_text`, `emotion`,
`mouth_action`, and `lip_sync_required=false`.

Real TTS, alignment, and lip-sync are deferred. The recommended story format is
narration-led with short character lines, which avoids relying on exact mouth
shapes during the mock milestone.

## Later ComfyUI Integration

The ComfyUI provider is a dry-run skeleton in the first milestone. Before real
integration, verify ComfyUI separately, then replace placeholder workflows in
`workflows/comfyui/` with reviewed local workflows. Model names, sources, and
licenses must be recorded in `data/models/models_manifest.json`.

## Later Seedance Integration

The Seedance provider is also dry-run only in the first milestone. Later work
should submit approved first-frame images and video prompts through a provider
that records task IDs, status, retry attempts, and output paths without leaking
API keys.

## Project Management Files

- `PLANS.md`: milestone plan and deferred work.
- `CURRENT_STATUS.md`: current environment and latest verification status.
- `REPO_MAP.md`: directory map for humans and agents.
- `docs/agent_skills.md`: multi-agent ownership, skills, and permissions.

## Repository

The local repository tracks `main` against:

```txt
git@github.com:boksic1986/cartoon.git
```

Generated files under `outputs/` are intentionally ignored and can be recreated
with the mock pipeline.

## Available Plugins

The current Codex session already has the useful official plugins enabled:
Browser Use, GitHub, and Superpowers. The MVP does not need extra plugin
installation. Browser Use is useful for later visual checks; GitHub is useful
after the repository is initialized; Superpowers is useful for planning,
execution, and verification workflows.

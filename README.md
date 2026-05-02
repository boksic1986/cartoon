# Idiom Video Studio

这是一个面向“成语故事短视频”的工程化生产流水线。第一阶段采用
mock-first 方案：不依赖真实图片 API、视频 API、TTS API、ComfyUI 服务或
任何真实 API key，也可以完整跑通本地流程。

## 使用 Conda 安装

```powershell
cd D:\pipeline\cartoon\idiom-video-studio
& D:\ProgramData\miniconda3\Scripts\conda.exe env create -f environment.yml
```

如果环境已经存在：

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pip install -e ".[dev]"
```

推荐在 Windows 上直接使用环境里的 `python.exe` 和 `idiom-video.exe`，这样不依赖
当前 PowerShell 是否已经激活 conda。需要交互式激活时，可以先初始化 conda，再运行
`conda activate idiom-video`。

## 国内源配置

本机开发环境建议使用稳定的国内镜像：

```powershell
D:\ProgramData\miniconda3\python.exe -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
D:\ProgramData\miniconda3\python.exe -m pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
```

Conda 通过 `C:\Users\11217\.condarc` 使用清华镜像，包括 defaults、
conda-forge、pytorch、nvidia 等频道。若清华 PyPI 临时不可用，可以把 pip
源切换到阿里云：`https://mirrors.aliyun.com/pypi/simple/`。

## 运行 Mock 流程

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data/idioms/shou-zhu-dai-tu.json --providers mock
```

输出目录：

```txt
outputs/shou-zhu-dai-tu/
```

关键产物：

```txt
01_script.json
02_storyboard.json
03_image_prompts.json
04_image_jobs.json
05_video_jobs.json
06_voice_jobs.json
audio/voice_assets.json
07_alignment.json
08_lipsync_jobs.json
quality_reports/prompt_quality.json
quality_reports/full_quality.json
review/script_review.json
review/image_review.json
review/video_review.json
subtitles/final.srt
final/metadata.json
final/final_mock.mp4 或 final/final_mock.txt
```

## 单步命令

```powershell
idiom-video validate-idiom data/idioms/shou-zhu-dai-tu.json
idiom-video generate-script data/idioms/shou-zhu-dai-tu.json
idiom-video generate-storyboard outputs/shou-zhu-dai-tu/01_script.json
idiom-video build-image-prompts outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video generate-images outputs/shou-zhu-dai-tu/03_image_prompts.json --provider mock
idiom-video generate-images outputs/shou-zhu-dai-tu/03_image_prompts.json --provider comfyui --dry-run --workflow workflows/comfyui/text2image_sdxl.placeholder.json
idiom-video comfyui-smoke-check outputs/shou-zhu-dai-tu --workflow workflows/comfyui/text2image_sdxl.reviewed.json --manifest data/models/models_manifest.json
idiom-video approve-images outputs/shou-zhu-dai-tu/images_raw --auto
idiom-video generate-videos outputs/shou-zhu-dai-tu/05_video_jobs.json --provider mock
idiom-video build-voice-jobs outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video generate-audio outputs/shou-zhu-dai-tu/06_voice_jobs.json --provider mock
idiom-video build-lipsync-jobs outputs/shou-zhu-dai-tu/07_alignment.json
idiom-video generate-subtitles outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video compose outputs/shou-zhu-dai-tu/
idiom-video publish-metadata outputs/shou-zhu-dai-tu/
idiom-video quality-check outputs/shou-zhu-dai-tu/
```

`build-image-prompts` 会写出 `quality_reports/prompt_quality.json`。第一阶段只检查正向
图片提示词是否包含禁用词；如果需要人工审查，会在生成图片前停止。`negative_prompt`
可以包含被排除的概念，因为它表达的是“不要生成这些内容”。

`quality-check` 会检查完整产物链路，并写出
`quality_reports/full_quality.json`。当前检查包括必需产物、核心 JSON schema
（`01_script.json`、`02_storyboard.json`、`03_image_prompts.json`、`04_image_jobs.json`、
`05_video_jobs.json`、`06_voice_jobs.json`、`07_alignment.json`、`08_lipsync_jobs.json`、
`final/metadata.json`）、prompt 质量报告、分镜时长、已审核图片和 mock 音频是否存在、
review 记录、模型 manifest 字段。核心 schema 会拒绝缺失字段和未知字段，避免人工编辑 JSON
时把拼写错误或临时字段带入后续流程。
如果存在 `comfyui_dry_run/jobs.json`，`quality-check` 也会校验 ComfyUI dry-run 任务结构、
workflow 路径和每个 request preview 文件是否存在。

## 审核记录

mock 阶段会生成可人工编辑的审核状态 JSON：

```txt
review/script_review.json
review/image_review.json
review/video_review.json
```

这些文件默认是 `auto=true` 和 `approved`，只表示 mock 流程自动通过。接入真实图片、
真实视频和真实配音后，人工审核者可以直接修改这些 JSON，记录 rejected、pending
和审核原因。

`quality-check` 会解析 review JSON。只要任一审核项是 `pending` 或 `rejected`，
完整质量检查就会失败，避免“有审核文件”被误认为“已经审核通过”。`approve-images --auto`
只会批准真实存在的 raw 图片；缺失图片会记录为 `pending`，不会生成对应视频任务。

## 对话、配音与口型

人物台词和旁白文本在 `01_script.json` 阶段确定。`02_storyboard.json` 会把旁白
或人物台词分配到具体镜头，并记录 `speaker_id`、`voice_text`、`subtitle_text`、
`emotion`、`mouth_action`、`lip_sync_required=false` 等字段。

真实 TTS、音频对齐和精确口型同步后续再接入。MVP 阶段推荐采用旁白驱动、人物短句
辅助的叙事方式，减少正脸长句说话镜头，让 mock 流程更稳定。

Phase 1.4 会把 `speech_cues` 转成 `06_voice_jobs.json`，`generate-audio --provider mock`
会写出可审查的 mock 音频文本资产和 `07_alignment.json`。`build-lipsync-jobs` 会写出
`08_lipsync_jobs.json` 和占位结果，默认 `enabled=false`，表示当前只记录口型任务，不做
真实口型渲染。

## 后续接入 ComfyUI

第一阶段的 ComfyUI provider 只支持 dry-run，不会访问本地 ComfyUI 服务，也不会生成真实图片。
可以先用下面命令检查 prompt、图片任务和 workflow 路径是否能组成可审查请求：

```powershell
idiom-video generate-images outputs/shou-zhu-dai-tu/03_image_prompts.json --provider comfyui --dry-run --workflow workflows/comfyui/text2image_sdxl.placeholder.json
```

该命令会写出：

```txt
outputs/shou-zhu-dai-tu/comfyui_dry_run/jobs.json
outputs/shou-zhu-dai-tu/images_raw/*.comfyui_dry_run.json
```

这些 JSON 只用于人工审核请求内容。真实接入前，需要先在本地单独完成 ComfyUI 冒烟测试，再把
`workflows/comfyui/` 里的 placeholder workflow 替换为已审核的本地 workflow。模型名称、来源和许可证
必须记录在 `data/models/models_manifest.json`。

替换真实 workflow 和 manifest 后，可以先运行离线冒烟检查：

```powershell
idiom-video comfyui-smoke-check outputs/shou-zhu-dai-tu --workflow workflows/comfyui/text2image_sdxl.reviewed.json --manifest data/models/models_manifest.json
```

该命令会写出 `quality_reports/comfyui_smoke_check.json`，检查 workflow JSON、模型许可证记录、
dry-run 请求预览和 workflow 引用是否一致。它不会打开 ComfyUI、不会访问 `127.0.0.1`、
也不会生成真实图片。详细步骤见 `docs/comfyui_smoke_checklist.md`。

## 后续接入 Seedance

第一阶段的 Seedance provider 也只保留 dry-run。后续真实接入时，应把审核通过的首帧图
和视频提示词交给 provider，并记录 task id、状态、重试次数和输出路径，同时避免泄露
API key。

## 项目管理文档

- `PLANS.md`：阶段计划和延后事项。
- `CURRENT_STATUS.md`：当前状态、环境和验证结果。
- `REPO_MAP.md`：仓库目录地图。
- `docs/agent_skills.md`：多 Agent 分工、技能使用和目录权限。
- `docs/comfyui_smoke_checklist.md`：ComfyUI 本地冒烟测试清单。

## Git 仓库

本地 `main` 分支跟踪：

```txt
git@github.com:boksic1986/cartoon.git
```

`outputs/` 下的生成产物默认忽略，不进入 git；需要时可通过 mock 流程重新生成。

## 可用插件

当前 Codex 会话已经启用 Browser Use、GitHub、Superpowers。MVP 不需要额外安装插件。
Browser Use 适合后续做可视化审查工具时使用；GitHub 适合仓库、PR 和 CI 工作流；
Superpowers 适合计划、执行和验证流程。

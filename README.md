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

如果需要在没有系统 FFmpeg 的机器上直接生成本地审片 MP4，可以额外安装可选视频依赖：

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pip install -e ".[video]"
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
09_review_video_plan.json
quality_reports/prompt_quality.json
quality_reports/full_quality.json
quality_reports/real_video_preflight.json
review/script_review.json
review/image_review.json
review/video_review.json
review/video_motion_review.json
review/review_packet.json
subtitles/final.srt
final/metadata.json
final/final_mock.mp4 或 final/final_mock.txt
final/review_v1.mp4 或 final/review_v1.gif
final/review_v1_manifest.json
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
idiom-video real-image-preflight outputs/shou-zhu-dai-tu --workflow workflows/comfyui/text2image_sdxl.reviewed.json --manifest data/models/models_manifest.json
idiom-video approve-images outputs/shou-zhu-dai-tu/images_raw --auto
idiom-video register-preview-images outputs/shou-zhu-dai-tu/real_images_preview_comedy_10 --approved
idiom-video generate-videos outputs/shou-zhu-dai-tu/05_video_jobs.json --provider mock
idiom-video generate-videos outputs/shou-zhu-dai-tu/05_video_jobs.json --provider seedance --dry-run
idiom-video build-video-motion-review outputs/shou-zhu-dai-tu --auto
idiom-video estimate-video-cost outputs/shou-zhu-dai-tu --unit-price-per-million-tokens 7 --currency USD
idiom-video build-voice-jobs outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video generate-audio outputs/shou-zhu-dai-tu/06_voice_jobs.json --provider mock
idiom-video build-lipsync-jobs outputs/shou-zhu-dai-tu/07_alignment.json
idiom-video build-review-packet outputs/shou-zhu-dai-tu/
idiom-video real-video-preflight outputs/shou-zhu-dai-tu/
idiom-video generate-subtitles outputs/shou-zhu-dai-tu/02_storyboard.json
idiom-video compose outputs/shou-zhu-dai-tu/
idiom-video build-review-video-plan outputs/shou-zhu-dai-tu/
idiom-video compose-review-video outputs/shou-zhu-dai-tu/
idiom-video compose-review-video outputs/shou-zhu-dai-tu/ --with-mock-audio
idiom-video publish-metadata outputs/shou-zhu-dai-tu/
idiom-video quality-check outputs/shou-zhu-dai-tu/
```

## Seedance 费用预估

在真实图生视频前，先运行离线费用预估：

```powershell
idiom-video estimate-video-cost outputs/shou-zhu-dai-tu --unit-price-per-million-tokens 7 --currency USD --retry-multiplier 1.2 --price-source "BytePlus ModelArk pricing" --price-source-url "https://docs.byteplus.com/docs/ModelArk/1099320" --price-checked-at "2026-05-03"
```

该命令只读取 `05_video_jobs.json`，不会调用 Seedance，也不需要 API key。它会写出
`quality_reports/seedance_cost_estimate.json`，记录镜头数量、总时长、分辨率、fps、估算 token 数、
单价、重试缓冲、价格来源 URL、复核日期和总费用。`real-video-preflight` 会要求该报告存在且与当前
`05_video_jobs.json` 一致；如果改了视频任务，必须重新运行 `estimate-video-cost`。

价格不要写进代码或测试。每次真实提交前，应以当前服务商控制台或官方价格页为准，把最新单价通过
`--unit-price-per-million-tokens` 传入。

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
workflow 路径和每个 request preview 文件是否存在；空的 jobs 列表会被视为失败，避免误把
“没有请求”当成“已经准备好”。
如果存在 `seedance_dry_run/jobs.json`，`quality-check` 会校验 Seedance dry-run 任务结构、
首帧图片路径和每个 request preview 文件是否存在；空的 jobs 列表同样会失败。
如果存在 `quality_reports/seedance_cost_estimate.json`，`quality-check` 会校验费用预估 schema，
并确认它仍匹配当前 `05_video_jobs.json`，避免改了时长或镜头数量后沿用旧预算。
如果存在 `review/video_motion_review.json`，`quality-check` 会校验每个镜头的运动审核项、
首帧图片路径、Seedance request preview 路径、背景连续性提示和审核状态。未带 `--auto`
生成的运动审核项会保持 `pending`，用于人工逐镜确认；进入完整质量门前需要人工改为
`approved`，或明确使用 `--auto` 只做离线技术检查通过。
如果存在 `review/review_packet.json`，`quality-check` 会校验审核包 schema、每个审核项状态和
引用的产物文件路径。
如果存在 `quality_reports/real_image_preflight.json`，`quality-check` 会校验真实图片生成前门禁报告；
未通过门禁时，完整质量检查也会失败。若该报告曾经通过，`quality-check` 会按报告里的 workflow
和 manifest 路径重新执行离线 preflight，防止人工审核后又改动 workflow 或模型记录。
如果存在 `quality_reports/real_video_preflight.json`，`quality-check` 会校验真实视频生成前门禁报告；
未通过门禁时，完整质量检查也会失败。若该报告曾经通过，`quality-check` 会重新执行离线
video preflight，防止人工审核后又改动 Seedance dry-run、运动审核或审核包。
如果存在 `09_review_video_plan.json` 或 `final/review_v1_manifest.json`，`quality-check`
也会校验本地审片视频计划、首帧图片引用、最终审片产物和 fallback 说明文件是否存在。

## 本地审片视频

在真实 Seedance 接入前，可以先把已经人工认可的首帧图拼成一个带字幕的本地审片版本。这个步骤只使用本地图片、Pillow 和可选 FFmpeg，不调用真实视频生成 API，也不需要 API key。

```powershell
idiom-video build-review-video-plan outputs/shou-zhu-dai-tu/
idiom-video compose-review-video outputs/shou-zhu-dai-tu/
```

该流程会写出：

```txt
outputs/shou-zhu-dai-tu/09_review_video_plan.json
outputs/shou-zhu-dai-tu/final/review_v1_manifest.json
outputs/shou-zhu-dai-tu/final/review_v1.mp4
```

如果系统或可选依赖中没有 FFmpeg，会自动生成：

```txt
outputs/shou-zhu-dai-tu/final/review_v1.gif
outputs/shou-zhu-dai-tu/final/review_v1_fallback.txt
```

这个本地审片版本用于检查剧情节奏、字幕、画面顺序和首帧连续性；它不是 Seedance 的真实运镜结果，也不代表口型同步或真实配音已经完成。

如果需要检查视频容器里是否已经有本地占位音轨，可以使用：

```powershell
idiom-video compose-review-video outputs/shou-zhu-dai-tu/ --with-mock-audio
```

该命令会生成 `audio/review_mock_track.wav`，并在 FFmpeg 可用时把它 mux 进
`final/review_v1.mp4`。这条音轨只是根据 speech cue 时间生成的本地 mock 节奏占位，
不是真实 TTS，不代表真实旁白、音效或口型同步已经完成。

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

如果已经通过人工视觉审核的是内置图像生成预览目录，可以用
`register-preview-images <preview_dir> --approved` 把这些 PNG 登记到 `images_raw` 和
`images_approved`，重写 `05_video_jobs.json`，并把 `review/image_review.json` 标为
`auto=false`。这一步不调用外部服务，只把人工认可的预览帧作为当前视频任务首帧输入。

可以用 `build-review-packet` 生成一个轻量 JSON 审核表单：

```powershell
idiom-video build-review-packet outputs/shou-zhu-dai-tu/
```

该命令会写出 `review/review_packet.json`，汇总剧本、图片、视频、配音和口型占位任务的
审核项、产物路径和检查清单。真实图片或真实视频接入后，人工审核者可以直接编辑这个 JSON；
只要存在 `pending`、`rejected` 或引用文件缺失，`quality-check` 就会失败。若已经生成
ComfyUI 或 Seedance dry-run，审核包会把对应的 jobs 清单和 request preview 一并列入审核项。
dry-run 产物生成或变更后，需要重新运行 `build-review-packet`；否则 `quality-check` 和
`real-image-preflight` 会认为审核包已经过期。

Seedance dry-run 之后，可以先生成视频运动审核表：

```powershell
idiom-video build-video-motion-review outputs/shou-zhu-dai-tu --auto
```

该命令会写出 `review/video_motion_review.json`，逐镜列出首帧图片、request preview、
运动提示词、背景连续性检查和审核状态。默认不带 `--auto` 时会写成 `pending`，
适合人工逐镜编辑；带 `--auto` 只表示离线技术检查通过，不代表真实视频效果已经通过人工审片。
如果该文件存在，`build-review-packet` 会把它纳入每个视频审核项。

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

当 ComfyUI dry-run、审核包和模型 manifest 都准备好后，再运行真实图片生成前门禁：

```powershell
idiom-video real-image-preflight outputs/shou-zhu-dai-tu --workflow workflows/comfyui/text2image_sdxl.reviewed.json --manifest data/models/models_manifest.json
```

该命令会写出 `quality_reports/comfyui_smoke_check.json` 和
`quality_reports/real_image_preflight.json`。如果通过，报告中的
`next_step` 会是 `STOP_BEFORE_REAL_IMAGE_GENERATION`，表示已经到达真实图片生成前的停止线；
此时应停下来由人工确认是否允许接入或调用真实 ComfyUI 生成。

## 后续接入 Seedance

第一阶段的 Seedance provider 只支持 dry-run，不会访问真实视频服务，也不会生成真实视频。
可以先用下面命令检查已审核首帧图和视频提示词是否能组成可审查请求：

```powershell
idiom-video generate-videos outputs/shou-zhu-dai-tu/05_video_jobs.json --provider seedance --dry-run
```

该命令会写出：

```txt
outputs/shou-zhu-dai-tu/seedance_dry_run/jobs.json
outputs/shou-zhu-dai-tu/videos/*.seedance_dry_run.json
```

这些 JSON 只用于人工审核请求内容。后续真实接入时，应把审核通过的首帧图和视频提示词交给
provider，并记录 task id、状态、重试次数和输出路径，同时避免泄露 API key。

在真实 Seedance provider 前，建议先运行：

```powershell
idiom-video build-video-motion-review outputs/shou-zhu-dai-tu
```

人工确认每个镜头的 `motion_prompt`、`image_path`、`request_preview_path` 和
`continuity_prompt_present` 后，再把状态改为 `approved`，或在只做本地技术闭环时使用
`--auto` 生成自动通过的审核记录。

当 Seedance dry-run、运动审核、统一审核包和费用预估都准备好后，再运行真实视频生成前门禁：

```powershell
idiom-video estimate-video-cost outputs/shou-zhu-dai-tu --unit-price-per-million-tokens 7 --currency USD
idiom-video real-video-preflight outputs/shou-zhu-dai-tu
```

该命令会写出 `quality_reports/real_video_preflight.json`。如果通过，报告中的
`next_step` 会是 `STOP_BEFORE_REAL_VIDEO_GENERATION`，表示已经到达真实视频生成前的停止线；
此时应停下来由人工确认是否允许接入或调用真实 Seedance 生成视频。
门禁会校验 `quality_reports/seedance_cost_estimate.json`、`seedance_dry_run/jobs.json` 与当前 `05_video_jobs.json` 的 scene、首帧、
prompt、时长和输出路径一致，避免修改视频任务后沿用旧 dry-run 请求。
报告还会记录当前产物指纹；`quality-check` 会用该指纹识别旧报告，相关 JSON 或引用文件
重新生成后需要重新运行 `estimate-video-cost` 和 `real-video-preflight`。

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

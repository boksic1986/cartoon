# 设计审查

## 可行性

项目说明中的 MVP 可行。最稳妥的第一阶段是离线 mock 流水线：每一步都输出可审查
JSON，同时生成 mock 图片、mock 视频、字幕、元数据和最终 fallback 成片文件。

## 保守取舍

- 使用 `04_image_jobs.json`，不使用 `04_comfyui_jobs.json`，让任务格式保持 provider 中立。
- `approve-images --auto` 负责生成 `05_video_jobs.json`，因为视频任务应引用已审核图片。
- ComfyUI、Seedance、OpenAI、真实 TTS 第一阶段只保留 dry-run 或 skeleton。
- 如果没有 FFmpeg，`compose` 写出 `final/final_mock.txt`，并给出清楚 warning。
- 环境文档以 conda 为主，因为后续 GPU、ComfyUI 和模型依赖更适合隔离环境。
- 核心文档采用中文表达，便于成语故事创作、提示词审查和人工审核。
- 人工审核仍以 JSON 为权威产物，后续 UI 或表单只能作为辅助入口。

## 对话、配音与口型

人物台词应在剧本阶段确定。分镜阶段负责把旁白或人物台词分配到镜头，并记录估算时间、
speaker、emotion、mouth_action。第一阶段只记录简单口型意图：
`mouth_action=speaking_simple`、`lip_sync_required=false`。

精确口型同步延后到后续 provider：

1. `VoiceProvider` 生成音频。
2. `AlignmentProvider` 生成 word、phoneme 或 viseme 时间轴。
3. `LipSyncProvider` 渲染口型同步片段。

MVP 应避免长时间正脸说话镜头，采用旁白驱动、短人物台词辅助的方式。
当前 Phase 1.4 只落地 mock-first 接口：`06_voice_jobs.json`、`audio/voice_assets.json`、
`07_alignment.json` 和 `08_lipsync_jobs.json`。真实 TTS、真实音频对齐和真实口型渲染仍然后置。

## 风险

- 真实 ComfyUI workflow 会受本地插件和模型版本影响。
- 当前 ComfyUI provider 只做 dry-run 请求预览，避免在 workflow、模型和许可证未确认时误调用真实服务。
- `comfyui-smoke-check` 只做离线准备检查，不探测本地端口，不提交 prompt，不轮询真实任务。
- 当前 Seedance provider 只做 dry-run 请求预览，真实任务提交、轮询和失败状态必须封装在 provider 后面。
- 精确口型同步需要单独的音频对齐和口型渲染阶段。
- 模型和素材许可证必须在发布前人工审查。

## 后续阶段

1. 通过本地 ComfyUI 冒烟测试后，再接真实图片 provider。
2. 先实现 Seedance dry-run 任务记录，再接真实提交。
3. 增加 TTS、音频对齐和可选口型同步 provider。
4. 单成语流程稳定后，再增加批量生产能力。

## 当前完成内容

- 项目结构、conda 环境文件、README、AGENTS 和项目管理文档已建立。
- Pydantic schema 覆盖成语资料、剧本、分镜、图片任务、视频任务、speech cue、字幕和发布元数据。
- 对话和配音文本在剧本阶段生成，再分配到分镜 speech cue。
- mock 图片、mock 视频、字幕、compose fallback、封面和元数据步骤均不依赖外部服务。
- `04_image_jobs.json` 保持 provider 中立，`05_video_jobs.json` 在图片审核后生成。
- `build-image-prompts` 会写出 prompt 质量报告，并阻断命中禁用词的正向提示词。
- `quality-check` 会写出完整质量报告，检查必需产物、核心 JSON schema、prompt 质量、
  已审核图片、review 记录和模型 manifest；核心 schema 会拒绝缺失字段和未知字段。
- mock 流程会生成 script、image、video 三类审核状态 JSON，后续可由人工修改。
- `quality-check` 不只检查 review 文件是否存在，也会解析每个 item 的状态；只要存在
  `pending` 或 `rejected` 就会失败。
- `approve-images --auto` 只批准真实存在的 raw 图片；缺图 scene 会写入 `pending`
  审核项，并且不会生成对应视频任务。
- `run-all` 会根据分镜 speech cue 生成 mock 配音任务、mock 音频资产、cue 级对齐记录和
  默认关闭的口型任务。
- `generate-images --provider comfyui --dry-run` 会生成 ComfyUI 请求预览 JSON，并由
  `quality-check` 校验 dry-run job、workflow 路径和 request preview 文件。
- `comfyui-smoke-check` 会在真实 provider 开发前检查 workflow JSON、模型 manifest、dry-run
  任务和 request preview 是否已经具备人工冒烟条件；placeholder 配置默认会被拦下。
- `generate-videos --provider seedance --dry-run` 会生成 Seedance 请求预览 JSON，并由
  `quality-check` 校验 dry-run job、首帧图片路径和 request preview 文件。
- `build-review-packet` 会生成 `review/review_packet.json`，把剧本、图片、视频、配音和口型
  占位任务整理成统一人工审核包；`quality-check` 会校验其 schema、状态和引用路径。

## 未完成内容

- 真实 ComfyUI API 调用、任务提交、轮询和真实图片下载。
- 本地 ComfyUI 前端中的真实 workflow 手动冒烟结果。
- 真实 Seedance API 调用。
- 真实 Seedance task id、任务轮询、失败重试和视频下载。
- 面向人工审核者的浏览器预览页或表单。
- 真实 TTS 音频、word/phoneme/viseme 级音频对齐和精确口型同步。
- 批量生产和发布自动化。

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
- Seedance dry-run 之后新增视频运动审核 JSON，用于在真实视频生成前逐镜确认首帧引用、运动提示词和背景连续性。
- 真实视频生成前新增 `real-video-preflight` 离线门禁；通过也只表示可以进入人工确认，不代表允许真实调用。
- 真实视频生成前新增 `estimate-video-cost` 离线费用报告；真实调用前必须人工确认价格来源、预算和是否允许外部调用。
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
- `real-image-preflight` 会生成 `quality_reports/real_image_preflight.json`，汇总检查真实图片生成前的
  离线门槛；通过后仍然停在真实 ComfyUI 调用前。
- Phase 1.9 加固后，`real-image-preflight` 也会写出 `quality_reports/comfyui_smoke_check.json`，
  并在 preflight 报告中记录 `smoke_report_path`，便于追溯失败原因。
- `build-review-packet` 在存在 ComfyUI / Seedance dry-run 产物时，会把 jobs 清单和 request preview
  纳入审核包，避免只审核 mock 结果而漏看真实 provider 请求内容。
- `quality-check` 会阻断空的 dry-run jobs，并会对已通过的真实图片 preflight 做当前 workflow /
  manifest 的一致性复验。
- 如果先生成审核包再生成 dry-run，`quality-check` 和 `real-image-preflight` 会把该审核包判定为过期，
  要求重新生成并审核包含 request preview 的包。
- 守株待兔样例已扩展为 10 镜头轻喜剧版本，剧本阶段包含旁白、人物短对白、情绪和简单口型意图。
- 分镜提示词已针对 10 镜头细化：兔子朝树桩方向奔跑、撞晕后安全躺地、等待阶段人物动作不重复、
  不在等待镜头中手持锄头，作物状态从翠绿、少量杂草、叶尖发黄到部分低垂循序渐进。
- 已用内置图像生成能力为守株待兔生成 `real_images_preview_comedy_10` 预览图和联系表，
  该目录仅供人工视觉审查，不替代正式 `images_raw` / `images_approved` provider 产物。
- 第二轮视觉反馈后，等待段进一步改成动作和季节双递进：坐着等待、趴着看小虫、
  躺着打盹、坐起醒悟；作物、大树叶色和远山色调分别随春末、初夏、夏末、初秋变化。
- 第三轮视觉反馈后，分镜提示词加入固定背景连续性：茅草屋始终在右后方靠山脚，
  屋前栅栏和水缸保持一致，田间小径从右下角经过树桩右侧通向房子，田垄方向和
  远山轮廓作为后续图片、视频生成的背景锚点。
- 新增 `register-preview-images <preview_dir> --approved`，用于把人工认可的内置图像预览
  登记为当前 `images_raw` / `images_approved` 首帧输入，并写出 `auto=false` 图片审核记录。
- 已基于登记后的首帧生成 Seedance dry-run 请求预览，人工审核包会包含 jobs 清单和每镜头
  request preview；重复 artifact path 会在审核包生成时去重，减少人工审核噪音。
- 新增 `build-video-motion-review`，会从 Seedance dry-run jobs 生成
  `review/video_motion_review.json`，逐镜记录首帧图片、request preview、运动提示词、时长、
  背景连续性检查和审核状态。
- `quality-check` 会在视频运动审核文件存在时校验 schema、文件引用、审核状态、背景连续性提示，
  并检查该审核文件是否仍与当前 Seedance dry-run jobs 一致。
- `build-review-packet` 会把 `review/video_motion_review.json` 纳入视频审核项，
  让统一审核包覆盖“从首帧到视频运动提示词”的人工复核。
- 新增 `real-video-preflight`，写出 `quality_reports/real_video_preflight.json`，集中检查视频任务、
  Seedance dry-run、运动审核和统一审核包；通过时仍停在 `STOP_BEFORE_REAL_VIDEO_GENERATION`。
- 新增 `estimate-video-cost`，写出 `quality_reports/seedance_cost_estimate.json`，用当前视频任务、目标分辨率、fps 和人工输入单价生成离线预算。
- `real-video-preflight` 与 `quality-check` 会校验费用报告与当前 `05_video_jobs.json` 指纹一致，防止改动任务后沿用旧预算。
- `quality-check` 会在真实视频门禁报告存在时校验 schema、`ok` 状态，并复验当前产物是否仍满足视频门禁。

## 未完成内容

- 真实 ComfyUI API 调用、任务提交、轮询和真实图片下载。
- 人工确认是否允许调用本地 ComfyUI 生成真实图片。
- 本地 ComfyUI 前端中的真实 workflow 手动冒烟结果。
- 真实 Seedance API 调用。
- 真实 Seedance task id、任务轮询、失败重试和视频下载。
- 对 `review/video_motion_review.json` 的逐镜人工审片确认。
- 对 `quality_reports/seedance_cost_estimate.json` 和 `quality_reports/real_video_preflight.json` 的人工确认，以及是否允许真实视频调用的明确授权。
- 面向人工审核者的浏览器预览页或表单。
- 真实 TTS 音频、word/phoneme/viseme 级音频对齐和精确口型同步。
- 批量生产和发布自动化。

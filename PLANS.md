# 项目计划

## MVP 目标

构建一条 mock-first 流水线，把单个成语资料 JSON 转换为可审查的中间 JSON、mock 图片、
mock 视频、字幕、发布元数据和最终 mock 成片文件。

## 当前阶段：Phase 1.1 加固

已完成：

1. 初始化 Python 3.11 项目。
2. 为所有核心 JSON 产物定义 Pydantic schema。
3. 实现确定性的剧本、分镜、提示词、provider、字幕和合成步骤。
4. 所有外部服务保留在 mock 或 dry-run 接口后面。
5. baseline 已推送到 `git@github.com:boksic1986/cartoon.git`。
6. 增加单步 CLI 流程测试。
7. `build-image-prompts` 阶段写出 prompt 质量报告。
8. 核心文档改为中文表达，更贴合成语故事语义。

下一步建议：

1. 为装有 FFmpeg 的机器补充可选冒烟测试说明。
2. 在真实 provider 开发前，先补 ComfyUI 本地冒烟测试清单。
3. 为真实图片/视频接入设计人工审核 UI 或轻量表单。

## 延后阶段

1. 通过本地冒烟测试后，再实现真实 ComfyUI 图片 provider。
2. Seedance dry-run 任务记录稳定后，再实现真实视频 provider。
3. 剧本和分镜 timing 稳定后，再接真实 TTS、音频对齐和口型同步 provider。

## Phase 1.2 审核闭环

已完成：

1. 增加 `quality-check` CLI，用于检查已生成产物。
2. 写出 `quality_reports/full_quality.json`。
3. mock 流程生成 `review/script_review.json`、`review/image_review.json`、
   `review/video_review.json`。
4. `approve-images --auto` 写入图片审核记录。
5. `quality-check` 会解析 review item 状态，遇到 `pending` 或 `rejected` 会失败。
6. `approve-images --auto` 不会批准缺失图片，缺图 scene 会记录为 `pending`。

## Phase 1.3 产物 schema 质量门

已完成：

1. `quality-check` 会逐一校验核心 JSON 产物：`01_script.json`、`02_storyboard.json`、
   `03_image_prompts.json`、`04_image_jobs.json`、`05_video_jobs.json`、`final/metadata.json`。
2. 任一核心产物缺字段、包含未知字段或结构不符合 Pydantic schema 时，`quality-check` 会失败，并在
   `quality_reports/full_quality.json` 写出对应 check 和问题路径。
3. 为损坏剧本、分镜、图片提示词、图片任务、视频任务、发布元数据和未知字段场景补充回归测试。

下一步建议：

1. 为 `quality-check` 增加可选的批量目录扫描，便于后续批量成语生产。
2. 为真实图片和真实视频接入前的人工审核 UI 设计 JSON 编辑约束。

## Phase 1.4 配音、音频对齐和口型任务接口

已完成：

1. 从 `02_storyboard.json` 的 `speech_cues` 生成 `06_voice_jobs.json`。
2. `generate-audio --provider mock` 写出可审查的 mock 音频文本资产和
   `audio/voice_assets.json`，不调用真实 TTS。
3. 生成 `07_alignment.json`，用 cue 级时间轴为后续 word、phoneme 或 viseme 对齐留接口。
4. 生成 `08_lipsync_jobs.json`，默认 `enabled=false`，只记录口型任务，不做真实口型渲染。
5. `run-all` 和 `quality-check` 已接入 voice、alignment、lip-sync 产物。

下一步建议：

1. 为真实 TTS provider 设计 voice id、语速、音色和授权记录字段。
2. 为音频对齐 provider 设计 word、phoneme、viseme 三种精度的可选输出。
3. 在真实图片风格稳定后，再评估是否接入精确口型同步渲染。

## Phase 1.5 ComfyUI 图片接入准备层

已完成：

1. 新增 `ComfyUIDryRunJob` schema，用于记录 ComfyUI 请求预览。
2. `generate-images --provider comfyui --dry-run` 会校验 workflow 路径，并写出
   `comfyui_dry_run/jobs.json` 和每个镜头的 request preview JSON。
3. dry-run provider 不访问 ComfyUI 服务，不生成真实图片，不需要 API key。
4. `quality-check` 会在 dry-run 产物存在时校验 dry-run schema、workflow 路径和 request preview 文件。

下一步建议：

1. 在本地 ComfyUI 手动跑通 placeholder 替换后的真实 workflow。
2. 在 `data/models/models_manifest.json` 记录真实图片模型、插件和许可证。
3. 冒烟测试稳定后，再实现真实 ComfyUI prompt 提交和结果轮询。

## Phase 1.6 ComfyUI 本地冒烟测试准备层

已完成：

1. 新增 `comfyui-smoke-check` CLI，用于在不连接 ComfyUI 的前提下检查本地冒烟测试准备状态。
2. 新增 `ModelManifest`、`ModelManifestEntry` 和 `ComfyUISmokeCheckReport` schema。
3. 冒烟检查会确认 workflow JSON、模型 manifest、dry-run 任务、request preview 文件和 workflow
   引用一致性。
4. 默认阻断仍包含 `placeholder` 或 `REVIEW_REQUIRED` 的 workflow / manifest，避免误把占位配置当作
   可真实生成配置。
5. 新增 `docs/comfyui_smoke_checklist.md`，说明真实 provider 开发前的人工作业步骤。

下一步建议：

1. 在本地安装并启动 ComfyUI，手动导入真实 workflow，完成一次图片生成冒烟。
2. 用真实 workflow 路径重新运行 `generate-images --provider comfyui --dry-run`，再运行
   `comfyui-smoke-check`。
3. 冒烟稳定后，再开发真实 ComfyUI provider：prompt 提交、任务轮询、图片下载和失败重试。

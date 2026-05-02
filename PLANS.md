# 项目计划

## MVP 目标

构建一条 mock-first 流水线，把单个成语资料 JSON 转换为可审查的中间 JSON、mock 图片、
mock 视频、字幕、发布元数据和最终 mock 成片文件。

## 当前阶段：Phase 2.1 守株待兔 10 镜头视觉方案

已完成：

1. 将守株待兔样例扩展为 10 镜头轻喜剧剧本，保留儿童向、旁白驱动和短对白。
2. 分镜补充兔子朝树桩奔跑、撞晕后安全躺地、等待动作差异和作物状态递进。
3. 等待段明确为春末、初夏、夏末、初秋的季节递进：坐着等待、趴着看小虫、
   躺着打盹、坐起醒悟。
4. 图片提示词加入固定背景连续性：茅草屋、屋前栅栏水缸、田间小径、树桩、
   田垄方向和远山轮廓保持一致。
5. 使用内置图像生成能力产出 `outputs/shou-zhu-dai-tu/real_images_preview_comedy_10/`
   预览图和联系表，供人工视觉审核；该目录仍是本地预览，不替代正式 provider 产物。
6. 为 10 镜头数量、轻喜剧文案、等待动作、季节递进、背景连续性和 review count
   补充回归测试。
7. 增加 `register-preview-images <preview_dir> --approved`，用于把人工认可的预览图登记为
   当前视频任务首帧输入，并写出 `auto=false` 的图片审核记录。

下一步建议：

1. 准备真实 ComfyUI 工作流和模型 manifest，先完成手动前端冒烟。
2. 冒烟通过后，再开发真实 ComfyUI provider；测试仍必须使用 mock HTTP 服务。
3. 基于已登记首帧生成 Seedance dry-run 请求预览，人工确认运动提示词后再考虑真实视频 provider。

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

## Phase 1.7 Seedance 视频接入准备层

已完成：

1. 新增 `SeedanceDryRunJob` schema，用于记录视频生成请求预览。
2. `generate-videos --provider seedance --dry-run` 会读取 `05_video_jobs.json`，并写出
   `seedance_dry_run/jobs.json` 和每个镜头的 request preview JSON。
3. dry-run provider 不访问真实视频服务，不生成真实视频，不需要 API key。
4. `quality-check` 会在 dry-run 产物存在时校验 Seedance dry-run schema、首帧图片路径和
   request preview 文件。

下一步建议：

1. 为真实 Seedance provider 设计 task id、状态、轮询间隔、失败原因和重试记录字段。
2. 真实视频接入前，补充视频任务的人工审核表单或 JSON 编辑约束。
3. 等真实图片风格稳定后，再用审核通过的首帧图片做 Seedance 手动冒烟测试。

## Phase 1.8 人工审核包

已完成：

1. 新增 `ReviewPacket` 和 `ReviewPacketItem` schema，用于约束可人工编辑的审核表单。
2. 新增 `build-review-packet` CLI，会从现有产物生成 `review/review_packet.json`。
3. 审核包会汇总剧本、图片、视频、配音和口型占位任务，并附带产物路径、状态和检查清单。
4. `quality-check` 会在审核包存在时校验 schema、审核状态和引用文件路径。

下一步建议：

1. 为审核包增加批量目录扫描，便于一次检查多个成语输出目录。
2. 后续可用 Browser Use 做一个只读预览页或轻量本地表单，但仍以 JSON 作为权威产物。
3. 真实图片/视频接入后，将人工审核结果写回 `review/review_packet.json` 和对应 review JSON。

## Phase 1.9 真实图片生成前门禁

已完成：

1. 新增 `RealImagePreflightReport` 和 `RealImagePreflightIssue` schema。
2. 新增 `real-image-preflight` CLI，用于汇总检查 prompt 质量、审核包、ComfyUI dry-run、workflow
   和模型 manifest。
3. 该命令只写出 `quality_reports/real_image_preflight.json`，不访问 ComfyUI，不提交真实图片任务。
4. 当报告通过时，`next_step=STOP_BEFORE_REAL_IMAGE_GENERATION`，表示已经到达真实图片生成前停止线。
5. `quality-check` 会在 preflight 报告存在时校验 schema 和 `ok` 状态。

下一步建议：

1. 停下来等待人工提供已审核真实 workflow、真实模型 manifest 和是否允许调用本地 ComfyUI 的确认。
2. 用户确认后，再设计真实 ComfyUI provider：提交 prompt、轮询结果、保存图片和失败重试。
3. 真实 provider 的测试仍必须使用 mock HTTP 服务，不能调用本机真实 ComfyUI。

## Phase 1.9 加固补充

已完成：

1. `real-image-preflight` 会同时写出 `quality_reports/comfyui_smoke_check.json`，并在
   `real_image_preflight.json` 中记录 `smoke_report_path`，方便人工追溯门禁失败原因。
2. `build-review-packet` 会在存在 ComfyUI / Seedance dry-run 产物时，把 jobs 清单和每个镜头的
   request preview 路径纳入审核包，避免只审核 mock 图片而漏看真实 provider 请求预览。
3. `quality-check` 会阻断空的 `comfyui_dry_run/jobs.json` 和空的 `seedance_dry_run/jobs.json`。
4. `quality-check` 和 `real-image-preflight` 会发现 dry-run 产物生成后未重新生成审核包的情况，提示先更新
   `review/review_packet.json`。
5. 对已经通过的 `real_image_preflight.json`，`quality-check` 会按报告里的 workflow 和 manifest
   重新执行离线 preflight，发现后续改动会失败并提示重新运行门禁。

停止线：

1. 当前阶段只推进到真实图片生成前门禁，不调用本地 ComfyUI，不提交真实图片任务。
2. 进入真实图片生成前，需要人工提供已审核 workflow、已审核模型 manifest、ComfyUI 前端手动冒烟结果，
   并明确授权调用本地 ComfyUI。

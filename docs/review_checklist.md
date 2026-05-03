# 审核清单

## 剧本审核

- 成语含义准确。
- 故事适合儿童和青少年观看。
- 人物台词短，适合配音。
- 即使没有精确口型同步，旁白也能承载故事。

## 图片审核

- 角色形象保持一致。
- 服装颜色和时代背景保持一致。
- 不出现现代品牌、logo、明星脸、公众人物肖像或具体版权角色。
- 不出现恐怖、血腥、成人化或其他不适合儿童教育动画的内容。
- 图片适合作为 image-to-video 首帧。
- 连续镜头中的关键背景锚点保持一致：房子位置、田间小径走向、树桩位置、田垄方向和远山轮廓不应明显跳变。
- 如果故事通过时间流逝表达后果，作物、树叶和远山色调应随季节渐进变化，而不是突然枯萎或突然换景。
- ComfyUI dry-run 只表示请求预览已生成，不代表真实图片已生成或已审核。
- 使用 ComfyUI dry-run 时，`comfyui_dry_run/jobs.json` 和每个 request preview JSON 都应可人工审查。
- 真实 ComfyUI provider 开发前，`quality_reports/comfyui_smoke_check.json` 应为 `ok=true`。
- workflow 和模型 manifest 不应继续包含 `placeholder` 或 `REVIEW_REQUIRED`。

## 视频审核

- 角色身份保持稳定。
- 动作温和自然。
- 不出现身份突变、画面融化、镜头剧烈不稳等问题。
- 镜头时长与旁白、字幕 cue 基本匹配。
- Seedance dry-run 只表示请求预览已生成，不代表真实视频已生成或已审核。
- 使用 Seedance dry-run 时，`seedance_dry_run/jobs.json` 和每个 request preview JSON 都应可人工审查。
- 如生成了 `review/video_motion_review.json`，应逐镜确认 `motion_prompt` 与首帧内容一致，
  `image_path` 和 `request_preview_path` 存在，`continuity_prompt_present=true`。
- 等待兔子的镜头应保持人物动作差异，不能简单重复站立或空等；作物、树叶和远山颜色应按时间渐进。
- `build-video-motion-review --auto` 只表示离线技术检查通过，不代表真实视频效果已经人工审片通过。
- 如果生成了 `09_review_video_plan.json`，应确认每个镜头的 `image_path` 指向当前认可的
  `images_approved` 首帧，字幕文本和起止时间与分镜一致。
- 如果生成了 `final/review_v1_manifest.json`，应确认 `output_path` 指向可打开的本地审片产物；
  当 `provider=pillow_gif_fallback` 时，还应确认 `fallback_note_path` 存在并说明没有使用 FFmpeg。
- 本地 `review_v1.mp4` 或 `review_v1.gif` 只用于检查镜头顺序、字幕节奏和首帧连续性，
  不代表真实 Seedance 运镜、真实配音或口型同步已经完成。
- v1 审片反馈中已发现第一镜和最后一镜略像；后续生成结尾图时应确认 `scene_10` 明显不同于清晨耕田：
  初秋傍晚、收起小板凳和草席、田垄侧面重新锄地、恢复中的新绿苗。
- 如果 `final/review_v1_manifest.json` 中 `has_audio=true`，应确认 `audio_path` 文件存在，
  并理解该音轨只是本地 mock 节奏占位，不是真实 TTS 或真实配音。

## 配音与口型审核

- `06_voice_jobs.json` 中每个 speech cue 都有对应配音任务。
- mock 音频资产只用于本地审核，不代表真实 TTS 结果。
- `07_alignment.json` 的 cue 时间与分镜 speech cue 基本一致。
- `08_lipsync_jobs.json` 当前默认 `enabled=false`，真实口型同步接入前不应误认为已经渲染。

## 发布审核

- 元数据不包含 API key 或本地敏感信息。
- 真实发布前，模型和素材许可证已经记录并审核。
- 最终产物存放在 `outputs/{idiom_slug}/` 下。
- 如生成了 `review/review_packet.json`，每个审核项都应是 `approved`，且引用文件存在。
- 如果使用内置图像生成预览作为当前首帧输入，应先运行
  `register-preview-images <preview_dir> --approved`，确认 `review/image_review.json` 为 `auto=false`，
  并抽查 `images_approved` 与预览目录对应 PNG 一致。
- 如生成了 `quality_reports/real_image_preflight.json`，其 `ok` 应为 `true`，且
  `next_step` 应为 `STOP_BEFORE_REAL_IMAGE_GENERATION`。
- `quality_reports/full_quality.json` 为 `ok=true`。
- `quality-check` 已通过核心 JSON schema 校验：剧本、分镜、图片提示词、图片任务、视频任务、
  配音任务、音频对齐、口型任务和发布元数据；缺失字段和未知字段都会阻断。
- 如存在 ComfyUI dry-run 产物，`quality-check` 已确认 workflow 路径和 request preview 文件存在。
- 如果准备进入真实 ComfyUI 冒烟阶段，`comfyui-smoke-check` 已确认 dry-run workflow 与本次检查的
  workflow 一致。
- 如存在 Seedance dry-run 产物，`quality-check` 已确认首帧图片路径和 request preview 文件存在。
- 如存在 `review/video_motion_review.json`，`quality-check` 已确认每个运动审核项为 `approved`，
  且首帧、request preview、背景连续性提示和 Seedance dry-run 一致。
- 如存在 `quality_reports/real_video_preflight.json`，其 `ok` 应为 `true`，且
  `next_step` 应为 `STOP_BEFORE_REAL_VIDEO_GENERATION`。
- 如果存在 `09_review_video_plan.json` 或 `final/review_v1_manifest.json`，`quality-check`
  应已确认审片计划 schema、首帧引用、最终输出和 fallback 说明文件存在。
- 如果本地审片 manifest 记录了 `has_audio=true`，`quality-check` 应已确认 `audio_path` 存在。
- `review/script_review.json`、`review/image_review.json`、`review/video_review.json`
  已由人工确认或明确保留 mock 自动审核状态。
- `review/review_packet.json` 已由人工确认，或明确保留 mock 自动审核状态。
- review item 不应存在 `pending` 或 `rejected`，除非当前阶段明确暂停发布。

## Phase 1.9 真实图片前门禁补充

- `quality_reports/real_image_preflight.json` 应记录 `smoke_report_path`，且对应的
  `quality_reports/comfyui_smoke_check.json` 文件应存在。
- 如果 `real_image_preflight.json` 的 `ok=true`，则 `next_step` 必须是
  `STOP_BEFORE_REAL_IMAGE_GENERATION`，并且仍需人工确认后才能调用本地 ComfyUI。
- 若 preflight 通过后修改了 workflow 或模型 manifest，必须重新运行 `real-image-preflight`；
  `quality-check` 应能发现这种后续改动并失败。
- 如存在 ComfyUI dry-run 产物，`comfyui_dry_run/jobs.json` 不应为空，且 jobs 清单和每个镜头的
  request preview 应进入 `review/review_packet.json` 的图片审核项。
- 如存在 Seedance dry-run 产物，`seedance_dry_run/jobs.json` 不应为空，且 request preview 应进入视频审核项。
- 真实视频生成前应先运行 `estimate-video-cost`，确认 `quality_reports/seedance_cost_estimate.json` 的单价、来源 URL、复核日期、重试缓冲和总费用。
- 真实视频生成前应先运行 `prepare-seedance-submit`，确认 `seedance_submit/submit_plan.json` 的预算上限、费用估算、首帧路径、request preview 和停止线。
- `seedance_submit/submit_plan.json` 不应包含 API key、请求密钥、账号标识或敏感请求头。
- 如存在 `seedance_tasks/submissions.json` 或 `seedance_tasks/results.json`，应确认它们仍为 mock 生命周期产物，且 task id、scene、输出路径和 `videos/seedance_clips.json` 对齐。
- 如使用 `--provider seedance --dry-run --confirm-external-call`，应确认产物中的 `client` 为 `mock_http`，且所有 submit/poll/download request/response 都是本地合同演练文件。
- `--provider seedance` 不带 `--dry-run` 且不带 `--execute-real` 时应被拒绝；真实 endpoint 只允许存在于 transport 配置中，不应写入产物 JSON。
- 真实调用必须显式使用 `--execute-real --confirm-external-call`，默认 `--max-real-tasks 1`，不要一次性提交全部镜头。
- 图生视频真实调用前应确认 `--image-url-map` 或 `--image-base-url` 指向可访问的公网首帧 URL；缺少 URL 时不得误用本地路径。
- 如使用 `--allow-text-only`，应记录这是文生视频接口试跑，不代表已按审核首帧完成图生视频。
- 真实下载完成后，确认 `videos/*.seedance_real.mp4` 存在，且 JSON 产物不包含 provider 凭证、鉴权请求头或临时远程下载链接。
- `seedance_tasks/*.json` 和 `videos/seedance_clips.json` 不应包含 API key、请求密钥、账号标识或敏感请求头。
- 任何 dry-run 产物生成或变更后，都应重新运行 `build-review-packet`，再进行 `quality-check` 或
  `real-image-preflight`。

## Phase 2.3 真实视频前门禁补充

- `quality_reports/real_video_preflight.json` 只表示离线门禁结果，不代表真实视频已生成。
- 如果 `real_video_preflight.json` 的 `ok=true`，则 `next_step` 必须是
  `STOP_BEFORE_REAL_VIDEO_GENERATION`，并且仍需人工确认后才能调用真实 Seedance。
- 若视频门禁通过后修改了 `seedance_dry_run/jobs.json`、`review/video_motion_review.json`
  、`review/review_packet.json` 或 `05_video_jobs.json`，必须重新运行 `estimate-video-cost`、`real-video-preflight` 和 `prepare-seedance-submit`；`quality-check`
  应能发现这种后续改动并失败。
- 若视频门禁通过后修改了 `05_video_jobs.json` 的首帧、prompt、时长或输出路径，也必须重新生成
  Seedance dry-run、运动审核、审核包和视频门禁报告。
- `05_video_jobs.json` 中的 `scene_id` 和 `job_id` 应保持唯一；重复项应被视为需要重新整理的视频任务。
- `real_video_preflight.json` 的产物指纹应与当前视频任务、Seedance dry-run、运动审核、
  审核包及其引用文件一致；`quality-check` 应能发现旧指纹。
- 若修改了 `seedance_submit/submit_plan.json`，必须重新运行 `submit-seedance-tasks` 和
  `poll-seedance-tasks`；`quality-check` 应能发现旧 task 指纹。

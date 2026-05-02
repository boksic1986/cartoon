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
- ComfyUI dry-run 只表示请求预览已生成，不代表真实图片已生成或已审核。
- 使用 ComfyUI dry-run 时，`comfyui_dry_run/jobs.json` 和每个 request preview JSON 都应可人工审查。
- 真实 ComfyUI provider 开发前，`quality_reports/comfyui_smoke_check.json` 应为 `ok=true`。
- workflow 和模型 manifest 不应继续包含 `placeholder` 或 `REVIEW_REQUIRED`。

## 视频审核

- 角色身份保持稳定。
- 动作温和自然。
- 不出现身份突变、画面融化、镜头剧烈不稳等问题。
- 镜头时长与旁白、字幕 cue 基本匹配。

## 配音与口型审核

- `06_voice_jobs.json` 中每个 speech cue 都有对应配音任务。
- mock 音频资产只用于本地审核，不代表真实 TTS 结果。
- `07_alignment.json` 的 cue 时间与分镜 speech cue 基本一致。
- `08_lipsync_jobs.json` 当前默认 `enabled=false`，真实口型同步接入前不应误认为已经渲染。

## 发布审核

- 元数据不包含 API key 或本地敏感信息。
- 真实发布前，模型和素材许可证已经记录并审核。
- 最终产物存放在 `outputs/{idiom_slug}/` 下。
- `quality_reports/full_quality.json` 为 `ok=true`。
- `quality-check` 已通过核心 JSON schema 校验：剧本、分镜、图片提示词、图片任务、视频任务、
  配音任务、音频对齐、口型任务和发布元数据；缺失字段和未知字段都会阻断。
- 如存在 ComfyUI dry-run 产物，`quality-check` 已确认 workflow 路径和 request preview 文件存在。
- 如果准备进入真实 ComfyUI 冒烟阶段，`comfyui-smoke-check` 已确认 dry-run workflow 与本次检查的
  workflow 一致。
- `review/script_review.json`、`review/image_review.json`、`review/video_review.json`
  已由人工确认或明确保留 mock 自动审核状态。
- review item 不应存在 `pending` 或 `rejected`，除非当前阶段明确暂停发布。

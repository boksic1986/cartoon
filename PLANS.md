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
3. 在接入 TTS 前补充音频和口型 provider 的 schema 草案。

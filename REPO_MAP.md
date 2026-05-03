# 仓库地图

## 根目录

- `README.md`：安装、运行和后续接入说明。
- `AGENTS.md`：Codex Agent 与协作者规则。
- `PLANS.md`：项目路线和当前阶段计划。
- `CURRENT_STATUS.md`：当前执行状态和验证命令。
- `REPO_MAP.md`：仓库目录地图。
- `pyproject.toml`：Python 包元数据和 CLI 入口。
- `environment.yml`：conda 环境定义。
- `outputs/`：CLI 生成的本地产物，默认被 git 忽略。

## 源码

- `src/idiom_video/schemas.py`：所有 JSON 产物的 Pydantic 契约。
- `src/idiom_video/config.py`：基于环境变量的配置。
- `src/idiom_video/cli.py`：Typer CLI。
- `src/idiom_video/script_writer.py`：成语资料生成剧本。
- `src/idiom_video/storyboard_writer.py`：剧本生成分镜。
- `src/idiom_video/prompt_builder.py`：分镜生成图片提示词和图片任务。
- `src/idiom_video/real_image_preflight.py`：真实图片生成前门禁报告。
- `src/idiom_video/real_video_preflight.py`：真实视频生成前门禁报告。
- `src/idiom_video/seedance_lifecycle.py`：Seedance mock 与 mock HTTP 任务提交、轮询和下载占位生命周期。
- `src/idiom_video/providers/seedance_client.py`：Seedance client contract 外壳、本地 mock HTTP transport 和禁用的真实网络 transport 占位。
- `src/idiom_video/seedance_submit.py`：真实 Seedance 提交前的离线提交计划和强确认校验。
- `src/idiom_video/voice_builder.py`：分镜 speech cue 生成配音、音频对齐和口型任务。
- `src/idiom_video/review_packet.py`：生成统一人工审核包。
- `src/idiom_video/video_motion_review.py`：生成 Seedance dry-run 运动提示词审核 JSON。
- `src/idiom_video/quality_rules.py`：质量检查和审核规则。
- `src/idiom_video/providers/`：mock 和 dry-run provider。
- `src/idiom_video/media/`：字幕、合成、审片视频、封面和元数据。
- `src/idiom_video/utils/`：路径、JSON、日志、重试工具。

## 数据与工作流

- `data/idioms/`：成语资料 JSON。
- `data/style/`：风格说明、负向提示词、禁用词。
- `data/models/`：模型许可证 manifest。
- `workflows/comfyui/`：后续真实 ComfyUI 工作流占位说明。
- `docs/agent_skills.md`：多 Agent 分工、技能使用和目录权限。
- `docs/comfyui_smoke_checklist.md`：ComfyUI 本地冒烟测试前的离线检查和人工步骤。
- `outputs/{idiom_slug}/quality_reports/`：生成的质量报告，默认被 git 忽略。
- `outputs/{idiom_slug}/quality_reports/real_image_preflight.json`：真实图片生成前门禁报告，默认被 git 忽略。
- `outputs/{idiom_slug}/quality_reports/real_video_preflight.json`：真实视频生成前门禁报告，默认被 git 忽略。
- `outputs/{idiom_slug}/quality_reports/seedance_cost_estimate.json`：真实视频生成前费用预估报告，默认被 git 忽略。
- `outputs/{idiom_slug}/quality_reports/comfyui_smoke_check.json`：ComfyUI 离线冒烟检查报告，默认被 git 忽略。
- `outputs/{idiom_slug}/real_images_preview_comedy_10/`：内置图像生成的本地视觉预览和联系表，
  用于人工审核风格、动作和场景连续性，默认被 git 忽略。
- `outputs/{idiom_slug}/review/`：生成的人工审核状态 JSON，默认被 git 忽略。
- `outputs/{idiom_slug}/review/review_packet.json`：统一人工审核包，默认被 git 忽略。
- `outputs/{idiom_slug}/review/video_motion_review.json`：视频运动提示词和首帧引用审核表，默认被 git 忽略。
- `outputs/{idiom_slug}/09_review_video_plan.json`：本地审片视频计划，默认被 git 忽略。
- `outputs/{idiom_slug}/final/review_v1_manifest.json`：本地审片视频输出清单，默认被 git 忽略。
- `outputs/{idiom_slug}/comfyui_dry_run/`：ComfyUI 请求预览清单，默认被 git 忽略。
- `outputs/{idiom_slug}/seedance_dry_run/`：Seedance 请求预览清单，默认被 git 忽略。
- `outputs/{idiom_slug}/seedance_submit/`：Seedance 提交计划，默认被 git 忽略。
- `outputs/{idiom_slug}/seedance_tasks/`：Seedance mock / mock HTTP 任务提交、轮询和下载响应账本，默认被 git 忽略。
- `outputs/{idiom_slug}/audio/`：mock 配音资产和配音资产清单，默认被 git 忽略。
- `outputs/{idiom_slug}/audio/review_mock_track.wav`：本地审片视频的 mock 节奏占位音轨，默认被 git 忽略。
- `outputs/{idiom_slug}/lipsync/`：mock 口型任务占位结果，默认被 git 忽略。

## 测试

- `tests/`：单元测试和集成测试。测试必须保持离线、mock-only。

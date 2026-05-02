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
- `src/idiom_video/voice_builder.py`：分镜 speech cue 生成配音、音频对齐和口型任务。
- `src/idiom_video/quality_rules.py`：质量检查和审核规则。
- `src/idiom_video/providers/`：mock 和 dry-run provider。
- `src/idiom_video/media/`：字幕、合成、封面和元数据。
- `src/idiom_video/utils/`：路径、JSON、日志、重试工具。

## 数据与工作流

- `data/idioms/`：成语资料 JSON。
- `data/style/`：风格说明、负向提示词、禁用词。
- `data/models/`：模型许可证 manifest。
- `workflows/comfyui/`：后续真实 ComfyUI 工作流占位说明。
- `docs/agent_skills.md`：多 Agent 分工、技能使用和目录权限。
- `docs/comfyui_smoke_checklist.md`：ComfyUI 本地冒烟测试前的离线检查和人工步骤。
- `outputs/{idiom_slug}/quality_reports/`：生成的质量报告，默认被 git 忽略。
- `outputs/{idiom_slug}/review/`：生成的人工审核状态 JSON，默认被 git 忽略。
- `outputs/{idiom_slug}/comfyui_dry_run/`：ComfyUI 请求预览清单，默认被 git 忽略。
- `outputs/{idiom_slug}/audio/`：mock 配音资产和配音资产清单，默认被 git 忽略。
- `outputs/{idiom_slug}/lipsync/`：mock 口型任务占位结果，默认被 git 忽略。

## 测试

- `tests/`：单元测试和集成测试。测试必须保持离线、mock-only。

# Agent 技能与目录所有权

本项目可以由单个 Codex 线程完成，也可以拆给多个 Agent 并行处理。并行时必须明确
目录和文件所有权。

## 当前可用官方插件

- Superpowers：用于计划、执行、TDD、验证和分支收尾。
- Browser Use：后续制作本地可视化审核工具或看板时使用。
- GitHub：用于仓库、PR、issue 和 CI 工作流。

MVP 阶段不需要额外安装插件。

## Agent 分工

| Agent | 技能重点 | 主要路径 | 权限 |
| --- | --- | --- | --- |
| Agent 1 | schema、config、CLI 基础 | `src/idiom_video/schemas.py`, `config.py`, `cli.py`, `utils/` | 修改核心契约前需要和其他 Agent 协调。 |
| Agent 2 | 剧本、分镜、提示词 | `script_writer.py`, `storyboard_writer.py`, `prompt_builder.py`, `data/idioms/`, `data/style/` | 负责故事文本、提示词模板和 speech cue 结构。 |
| Agent 3 | 图片 provider | `providers/base.py`, `providers/image_mock.py`, `providers/image_comfyui.py`, `workflows/comfyui/` | 可增加 dry-run 字段；测试不得调用真实服务。 |
| Agent 4 | 视频、TTS、字幕、合成 | `providers/video_mock.py`, `providers/video_seedance.py`, `providers/tts_mock.py`, `media/` | 负责缺少 FFmpeg 或真实 provider 时的 fallback。 |
| Agent 5 | 质量与审核 | `quality_rules.py`, `docs/review_checklist.md`, `data/models/` | 负责版权、适龄和模型许可证检查。 |
| Agent 6 | 文档与验证 | `README.md`, `AGENTS.md`, `PLANS.md`, `CURRENT_STATUS.md`, `REPO_MAP.md`, `tests/` | 负责安装说明、测试命令和最终验证记录。 |

## 协作规则

- 不回滚其他 Agent 的改动。
- 生成产物统一放到 `outputs/{idiom_slug}/`。
- 测试保持离线和 mock-only。
- 示例聚焦 AI 动画生产，不加入无关技术主题。
- 真实 API key 不得写入代码、文档、日志、测试或示例。

# Agent 规则

## 项目范围

本仓库用于制作“成语故事短视频”的 AI 动画生产流水线。所有示例、提示词、文档和工具
说明都应聚焦动画制作、媒体生成、人工审核和发布元数据，不添加与本项目无关的技术主题。

## 工程规则

- 使用 Python 3.11+。
- 核心 JSON 产物必须使用 Pydantic 定义 schema。
- CLI 使用 Typer。
- 测试使用 pytest。
- 所有外部服务必须封装为 provider。
- 每个 provider 必须支持 mock 或 dry-run。
- 测试不得调用真实外部服务。
- 不得在代码、文档、测试、日志或示例输出中写入真实 API key。
- 路径处理保持 Windows 兼容，优先使用 `pathlib.Path`。
- 每个中间产物都应是可人工审查的 JSON。

## 内容与版权边界

- 不请求或模仿具体版权角色。
- 不请求明星脸、公众人物脸或真人肖像。
- 不模仿具体在世艺术家风格。
- 画面应适合儿童教育动画，温和、清晰、可审查。
- 发布前必须审查 LoRA、模型和素材许可证。

## 多 Agent 分工

多 Agent 协作时必须明确文件所有权：

- Agent 1：schema、config、CLI 基础、utils。
- Agent 2：script writer、storyboard writer、prompt builder、成语和风格数据。
- Agent 3：图片 provider base、mock 图片 provider、ComfyUI dry-run skeleton。
- Agent 4：视频 provider、TTS mock、字幕、合成、元数据。
- Agent 5：质量规则、禁用词、审核清单、模型 manifest。
- Agent 6：README、项目管理文档、测试、最终验证。

Agent 不得回滚其他 Agent 的改动。如果文件存在混合所有权，先协调再修改。

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

1. 增加独立 `quality-check` CLI 命令，用于检查已经生成的产物。
2. 为装有 FFmpeg 的机器补充可选冒烟测试说明。
3. 在真实 provider 开发前，先补 ComfyUI 本地冒烟测试清单。

## 延后阶段

1. 通过本地冒烟测试后，再实现真实 ComfyUI 图片 provider。
2. Seedance dry-run 任务记录稳定后，再实现真实视频 provider。
3. 剧本和分镜 timing 稳定后，再接真实 TTS、音频对齐和口型同步 provider。

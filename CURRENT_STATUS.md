# 当前状态

状态：Phase 1.4 配音、音频对齐和口型任务接口开发中。

## Git

- 分支：`codex/phase-1.4-voice-lipsync`
- 远端：`git@github.com:boksic1986/cartoon.git`
- 已推送 baseline：`f524fe9 chore: initialize mock idiom video pipeline`
- 已合并功能提交：`846e744 Merge pull request #2 from boksic1986/codex/full-artifact-schema-check`

## 环境

- Conda 路径：`D:\ProgramData\miniconda3`
- 推荐环境名：`idiom-video`
- Python 版本：3.11
- Pip 源：清华 PyPI 镜像
- Conda 源：清华 defaults 和 cloud 镜像

## 当前约束

- mock 模式必须不依赖网络调用。
- 测试不得调用真实外部服务。
- 真实 API key 不得出现在代码、文档、测试、日志或示例输出中。
- 本项目只服务 AI 动画生产流程，提示词、流程和工具说明都应聚焦该领域。

## 验证命令

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe quality-check outputs\shou-zhu-dai-tu
```

最近验证：

- `D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`：43 passed。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock`：生成了预期的 `outputs/shou-zhu-dai-tu/` 产物。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe quality-check outputs\shou-zhu-dai-tu`：通过。
- `outputs/shou-zhu-dai-tu/quality_reports/prompt_quality.json`：`ok=true`，无问题。
- `outputs/shou-zhu-dai-tu/quality_reports/full_quality.json`：`ok=true`，无问题。
- `outputs/shou-zhu-dai-tu/audio/voice_assets.json`：生成 7 条 mock 配音资产记录。

## 当前加固内容

- `build-image-prompts` 会写出 `quality_reports/prompt_quality.json`。
- 正向图片提示词包含禁用词时会阻断流程。
- 单步 CLI 流程已纳入集成测试。
- 核心项目文档已中文化，以便更贴合成语故事创作和人工审查。
- `quality-check` 会写出 `quality_reports/full_quality.json`。
- mock 流程会写出 `review/script_review.json`、`review/image_review.json`、
  `review/video_review.json`。
- `quality-check` 会解析审核状态，`pending` 或 `rejected` 会导致检查失败。
- 缺失 raw 图片不会被自动批准，会在 `image_review.json` 中记录为 `pending`。
- `quality-check` 会逐一校验核心 JSON schema：剧本、分镜、图片提示词、图片任务、视频任务和发布元数据；缺失字段和未知字段都会失败。
- `run-all` 会生成 `06_voice_jobs.json`、`audio/voice_assets.json`、`07_alignment.json` 和
  `08_lipsync_jobs.json`。
- 当前配音和口型同步仍是 mock-only：生成文本资产和任务记录，不调用真实 TTS 或口型渲染服务。

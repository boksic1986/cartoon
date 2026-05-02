# 当前状态

状态：Phase 1.1 加固中。

## Git

- 分支：`main`
- 远端：`git@github.com:boksic1986/cartoon.git`
- 已推送 baseline：`f524fe9 chore: initialize mock idiom video pipeline`
- 最新功能提交：`b5e2919 feat: add prompt quality gate`

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
```

最近验证：

- `D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`：17 passed。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock`：生成了预期的 `outputs/shou-zhu-dai-tu/` 产物。
- `outputs/shou-zhu-dai-tu/quality_reports/prompt_quality.json`：`ok=true`，无问题。

## 当前加固内容

- `build-image-prompts` 会写出 `quality_reports/prompt_quality.json`。
- 正向图片提示词包含禁用词时会阻断流程。
- 单步 CLI 流程已纳入集成测试。
- 核心项目文档已中文化，以便更贴合成语故事创作和人工审查。

# ComfyUI 工作流占位

这些文件是 mock-first 阶段的 placeholder，只说明后续需要哪些工作流槽位，并不是可直接
运行的真实 ComfyUI graph。

真实 ComfyUI 接入需要等本地冒烟测试通过后再做。替换 workflow 前，必须先在
`data/models/models_manifest.json` 中记录模型来源、版本和许可证。

当前可用的 `--provider comfyui --dry-run` 只会读取 workflow 路径并写出请求预览 JSON，
不会连接 `COMFYUI_BASE_URL`，也不会向 ComfyUI 提交任务。真实接入前，请先确认本地
workflow、节点插件、模型文件和许可证记录都已经人工审核。

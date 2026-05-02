# ComfyUI 本地冒烟测试清单

本清单用于从 dry-run 过渡到真实 ComfyUI 图片生成前的人工检查。当前项目代码只提供
离线检查命令，不连接本地 ComfyUI，不提交 prompt，不轮询结果。

## 前置条件

1. 本机已经能单独启动 ComfyUI，并能在浏览器打开本地前端。
2. `workflows/comfyui/` 中已经替换为人工审核过的真实 workflow JSON。
3. `data/models/models_manifest.json` 已记录模型名称、类型、本地路径、来源、许可证和
   `commercial_use_allowed`。
4. 已先运行 `generate-images --provider comfyui --dry-run`，生成可审查请求预览。

## 离线检查命令

```powershell
idiom-video comfyui-smoke-check outputs/shou-zhu-dai-tu `
  --workflow workflows/comfyui/text2image_sdxl.reviewed.json `
  --manifest data/models/models_manifest.json
```

命令会写出：

```txt
outputs/shou-zhu-dai-tu/quality_reports/comfyui_smoke_check.json
```

检查内容：

- workflow 文件存在且是合法 JSON。
- workflow 和模型 manifest 不再包含 `placeholder` 或 `REVIEW_REQUIRED`。
- manifest 中每个模型都有明确的 `commercial_use_allowed`。
- `comfyui_dry_run/jobs.json` 存在、结构正确且不为空。
- dry-run 任务引用的 workflow 与本次检查的 workflow 一致。
- 每个 request preview JSON 文件都存在，便于人工审查。

## 手动冒烟建议

离线检查通过后，再在 ComfyUI 前端中人工执行一次真实 workflow：

1. 打开本地 ComfyUI 前端。
2. 导入已审核 workflow。
3. 使用 `comfyui_dry_run/jobs.json` 中任意一个镜头的 prompt、negative prompt、seed、
   width 和 height。
4. 确认能生成一张符合成语故事风格的图片。
5. 把实际使用的 workflow 文件和模型 manifest 固定下来，再进入真实 provider 开发。

如果仍在 placeholder 阶段，只能使用 `--allow-placeholders` 做格式预检；该结果不能作为
真实图片生成准备完成的依据。

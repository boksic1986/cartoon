# Seedance 真实调用运行手册

本手册用于从本地 mock / dry-run 产物推进到真实 Seedance API 调用。它只适用于已经通过人工审核的项目输出目录。

## 前置条件

1. 已完成并审核 `outputs/{slug}/05_video_jobs.json`、`seedance_dry_run/jobs.json`、`review/video_motion_review.json`、`review/review_packet.json`。
2. 已运行并确认：

   ```powershell
   idiom-video estimate-video-cost outputs\shou-zhu-dai-tu --unit-price-per-million-tokens 7 --currency USD
   idiom-video real-video-preflight outputs\shou-zhu-dai-tu
   idiom-video prepare-seedance-submit outputs\shou-zhu-dai-tu --max-cost 5 --confirm-external-call
   ```

3. 已在当前 shell 或 `.env` 中设置 `ARK_API_KEY` 或 `SEEDANCE_API_KEY`。不要把真实值写入文档、测试、日志或 JSON 产物。
4. 如果要做图生视频，首帧图片必须有服务商可访问的公网 URL。可用 `--image-url-map` 提供 scene 到 URL 的映射：

   ```json
   {
     "scene_01": "https://example.com/scene_01.png"
   }
   ```

   如果没有公网首帧 URL，只能显式传入 `--allow-text-only` 做文生视频试跑。

## 推荐试跑：只提交 1 个镜头

默认先只提交 1 个任务，控制费用和风险：

```powershell
idiom-video submit-seedance-tasks outputs\shou-zhu-dai-tu `
  --provider seedance `
  --execute-real `
  --confirm-external-call `
  --max-real-tasks 1 `
  --image-url-map outputs\shou-zhu-dai-tu\seedance_submit\image_url_map.json
```

如果暂时没有公网首帧 URL，并且你接受先做文生视频验证接口，可用：

```powershell
idiom-video submit-seedance-tasks outputs\shou-zhu-dai-tu `
  --provider seedance `
  --execute-real `
  --confirm-external-call `
  --max-real-tasks 1 `
  --allow-text-only
```

提交成功后再轮询并下载：

```powershell
idiom-video poll-seedance-tasks outputs\shou-zhu-dai-tu `
  --provider seedance `
  --execute-real `
  --confirm-external-call `
  --poll-interval-seconds 5 `
  --max-poll-attempts 60
```

## 产物与安全边界

- `seedance_tasks/*.real.*.json` 会记录 submit / poll / download 的可审核 request-response 摘要。
- JSON 产物不会写入 provider 凭证、鉴权请求头或临时远程下载链接。
- 下载后的视频会写入 `outputs/{slug}/videos/*.seedance_real.mp4`，并刷新 `videos/seedance_clips.json`。
- 每次真实调用后都要运行：

  ```powershell
  idiom-video quality-check outputs\shou-zhu-dai-tu
  ```

## 失败处理

- 缺少 `ARK_API_KEY` 或 `SEEDANCE_API_KEY`：命令会在真实请求前停止。
- 未提供公网首帧 URL：命令会停止，除非显式使用 `--allow-text-only`。
- 费用或审核产物变更：重新运行费用估算、视频门禁和提交计划。
- 任务失败或超时：保留当前 JSON 产物，先人工查看错误信息，不要盲目批量重试。

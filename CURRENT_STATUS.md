# 当前状态
状态：Phase 2.10 Seedance 真实 transport 与单镜头试跑门禁开发中。

## 2026-05-04 Phase 2.10 Seedance 真实 transport 与单镜头试跑门禁

- 当前分支：`codex/phase-2.10-real-seedance-transport`。
- 新增真实 Seedance HTTP transport：默认 base URL 为 `https://ark.ap-southeast.bytepluses.com/api/v3`，API key 只从 `ARK_API_KEY`、`SEEDANCE_API_KEY` 或 `BYTEPLUS_ARK_API_KEY` 读取。
- `submit-seedance-tasks --provider seedance --execute-real --confirm-external-call` 才会进入真实提交路径；默认 `--max-real-tasks 1`，避免一次性提交全部镜头。
- 图生视频需要 `--image-url-map` 或 `--image-base-url` 提供公网首帧 URL；如果没有公网 URL，默认阻断，除非显式 `--allow-text-only` 做文生视频试跑。
- `poll-seedance-tasks --provider seedance --execute-real --confirm-external-call` 会轮询真实任务并下载到 `videos/*.seedance_real.mp4`，JSON 产物不会写 provider 凭证或临时远程下载链接。
- 当前本地 shell 未检测到 `ARK_API_KEY`、`SEEDANCE_API_KEY` 或 `BYTEPLUS_ARK_API_KEY`，所以真实调用会停在凭证门禁。

## 2026-05-03 Phase 2.9 Seedance mock HTTP 客户端外壳

- 当前分支：`codex/phase-2.9-seedance-client-shell`。
- 新增 `SeedanceClientSubmitRequest`、`SeedanceClientSubmitResponse`、`SeedanceClientPollRequest`、`SeedanceClientPollResponse`、`SeedanceClientDownloadRequest` 和 `SeedanceClientDownloadResponse` schema，用于约束未来真实 provider 的 request/response 合同。
- 新增 `src/idiom_video/providers/seedance_client.py`，包含 `SeedanceApiClient`、本地 `MockSeedanceHttpTransport` 和默认禁用的真实网络 transport 占位。
- `submit-seedance-tasks --provider seedance --dry-run --confirm-external-call` 会写出本地 mock HTTP submit request/response 和 `seedance_tasks/submissions.json`，不会读取 API key，也不会发起网络请求。
- `poll-seedance-tasks --provider seedance --dry-run --confirm-external-call` 会写出本地 mock HTTP poll/download request/response、占位视频文本和 `videos/seedance_clips.json`。
- `quality-check` 已扩展为同时校验 mock 与 mock HTTP 生命周期产物，并扫描新 request/response 中的敏感字符串。

停止线：不带 `--dry-run` 的 `--provider seedance` 仍会拒绝；当前阶段不实现真实 endpoint、鉴权、网络提交、真实轮询、真实下载或真实计费回填。

## 2026-05-03 Phase 2.8 Seedance mock 任务生命周期

- 当前分支：`codex/phase-2.8-seedance-mock-lifecycle`。
- 新增 `submit-seedance-tasks outputs\shou-zhu-dai-tu --provider mock`，只生成本地 mock submissions 和逐镜 submit request/response JSON。
- 新增 `poll-seedance-tasks outputs\shou-zhu-dai-tu --provider mock`，只生成本地 mock poll/download response、占位视频文本和 `videos/seedance_clips.json`。
- `--provider seedance` 当前仍会拒绝，避免触发真实外部视频任务。
- `quality-check` 在 task 产物存在时校验 schema、提交计划指纹、task/result 一致性、clips manifest 和本地输出文件。
- task artifacts 与 clips manifest 会被扫描敏感字符串，避免凭证、敏感请求头或账号标识进入 JSON。

状态：Phase 2.7 Seedance 提交计划与强确认骨架开发中。

## 2026-05-03 Phase 2.7 Seedance 提交计划与强确认骨架

- 当前分支：`codex/phase-2.7-seedance-submit-gate`。
- 新增 `prepare-seedance-submit outputs\shou-zhu-dai-tu --max-cost <amount> --confirm-external-call`。
- 该命令只生成 `seedance_submit/submit_plan.json`，不会提交真实 Seedance 任务，不轮询，不下载真实视频。
- `--confirm-external-call` 是人工理解下一阶段可能外部调用的确认；当前阶段即使传入 `--execute-real` 也会被拒绝。
- 提交计划不写入 API key、请求密钥、账号标识或敏感请求头。
- `quality-check` 会在提交计划存在时校验 schema、费用上限和当前真实视频门禁指纹一致性。

状态：Phase 2.6 真实视频费用门禁开发中。

## 2026-05-03 Phase 2.6 真实视频费用门禁

- 当前分支：`codex/phase-2.6-video-cost-gate`。
- 新增 `estimate-video-cost outputs\shou-zhu-dai-tu --unit-price-per-million-tokens <price> --currency USD`。
- 该命令只读取本地 `05_video_jobs.json`，不会调用 Seedance，不需要 API key。
- 新增产物：`quality_reports/seedance_cost_estimate.json`，记录 clip 数、总时长、分辨率、fps、估算 token、单价、重试缓冲、价格来源、来源 URL、人工复核日期和视频任务指纹。
- `quality-check` 会在费用报告存在时校验 schema，并确认费用报告与当前 `05_video_jobs.json` 一致。
- `real-video-preflight` 现在要求费用报告存在且未过期；真实视频生成仍停在 `STOP_BEFORE_REAL_VIDEO_GENERATION`，不会自动调用真实 Seedance。

状态：Phase 2.5 审片反馈闭环与本地 mock 音轨开发中。

## Git

- 分支：`codex/phase-2.5-audio-review-video`
- 远端：`git@github.com:boksic1986/cartoon.git`
- 已推送 baseline：`f524fe9 chore: initialize mock idiom video pipeline`
- 已合并功能提交：`1bfb989 Merge pull request #13 from boksic1986/codex/phase-2.4-local-review-video`

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
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe compose-review-video outputs\shou-zhu-dai-tu
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe compose-review-video outputs\shou-zhu-dai-tu --with-mock-audio
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe quality-check outputs\shou-zhu-dai-tu
```

## 2026-05-03 Phase 2.5 审片反馈闭环与本地 mock 音轨

- 当前分支：`codex/phase-2.5-audio-review-video`。
- v1 审片反馈：第一张图和最后一张略像，其他镜头暂无明显问题。
- 已将 `scene_10` 分镜提示改为初秋傍晚、收起小板凳和草席、田垄侧面重新锄地、恢复中的新绿苗，避免后续图片生成继续贴近第一镜。
- 新增 `compose-review-video --with-mock-audio`，生成 `audio/review_mock_track.wav`，并在 FFmpeg 可用时 mux 进 `final/review_v1.mp4`。
- `final/review_v1_manifest.json` 会记录 `has_audio` 与 `audio_path`；`quality-check` 会检查音频文件存在。
- 本地 mock 音轨只是节奏占位，不是真实 TTS，不代表真实旁白、音效或口型同步完成。

## 2026-05-03 Phase 2.4 本地审片视频

- 新增目标：基于 `images_approved` 中已登记的守株待兔 10 张中国风卡通首帧，生成第一版可本地观看的审片视频。
- 新增产物：`09_review_video_plan.json`、`final/review_v1_manifest.json`、`final/review_v1.mp4` 或 `final/review_v1.gif`。
- 新增命令：`build-review-video-plan` 和 `compose-review-video`。
- `compose-review-video` 优先使用本地 FFmpeg 或可选 `imageio-ffmpeg` 生成 MP4；没有 FFmpeg 时使用 Pillow 写出 GIF fallback 和说明文件。
- 本阶段不调用真实 Seedance、ComfyUI、OpenAI 或 TTS 服务；本地审片版只用于检查镜头顺序、字幕节奏和首帧连续性。

最近验证：

- `D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`：110 passed。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe compose-review-video outputs\shou-zhu-dai-tu --with-mock-audio`：已生成带本地 mock 音轨的 `final/review_v1.mp4`。
- `final/review_v1_manifest.json`：`provider=local_ffmpeg`、`has_audio=true`、`audio_path=audio/review_mock_track.wav`。
- FFmpeg 检测：`review_v1.mp4` 包含 H.264 视频流和 AAC mono 音频流，时长 51 秒。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock`：生成了预期的 `outputs/shou-zhu-dai-tu/` 产物。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe quality-check outputs\shou-zhu-dai-tu`：通过。
- `outputs/shou-zhu-dai-tu/quality_reports/prompt_quality.json`：`ok=true`，无问题。
- `outputs/shou-zhu-dai-tu/quality_reports/full_quality.json`：`ok=true`，无问题。
- `outputs/shou-zhu-dai-tu/audio/voice_assets.json`：生成 7 条 mock 配音资产记录。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe generate-images outputs\shou-zhu-dai-tu\03_image_prompts.json --provider comfyui --dry-run --workflow workflows\comfyui\text2image_sdxl.placeholder.json`：生成 6 条 ComfyUI 请求预览 JSON，不调用真实服务。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe comfyui-smoke-check outputs\shou-zhu-dai-tu --workflow workflows\comfyui\text2image_sdxl.placeholder.json --manifest data\models\models_manifest.json`：按预期失败，并写出 placeholder / manifest 待审核问题。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe generate-videos outputs\shou-zhu-dai-tu\05_video_jobs.json --provider seedance --dry-run`：生成 6 条 Seedance 请求预览 JSON，不调用真实服务。
- Seedance dry-run 产物存在时，`quality-check outputs\shou-zhu-dai-tu` 通过。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe build-review-packet outputs\shou-zhu-dai-tu`：生成 `review/review_packet.json`。
- 审核包产物存在时，`quality-check outputs\shou-zhu-dai-tu` 通过。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe real-image-preflight outputs\shou-zhu-dai-tu --workflow workflows\comfyui\text2image_sdxl.placeholder.json --manifest data\models\models_manifest.json`：按预期失败，提示 placeholder / manifest 仍未达到真实图片生成门槛。

## 2026-05-02 Phase 1.9 加固状态

- 当前分支：`codex/phase-1.9-real-image-preflight`。
- 最新完整测试：`D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`，结果为 `75 passed in 4.90s`。
- `run-all data\idioms\shou-zhu-dai-tu.json --providers mock` 已在默认 `outputs/shou-zhu-dai-tu/` 跑通。
- 清理旧版 preflight 报告后，`quality-check outputs\shou-zhu-dai-tu` 已通过；旧报告失败原因是 schema 已新增
  `smoke_report_path` 字段。
- `generate-images --provider comfyui --dry-run` 和 `generate-videos --provider seedance --dry-run` 已生成 request preview，
  未调用真实外部服务。
- `build-review-packet outputs\shou-zhu-dai-tu` 会把 dry-run jobs 和 request preview 纳入审核包。
- 若 dry-run 产物是在审核包之后生成，`quality-check` 和 `real-image-preflight` 会判定审核包过期，要求重新运行
  `build-review-packet`。
- `real-image-preflight outputs\shou-zhu-dai-tu --workflow workflows\comfyui\text2image_sdxl.placeholder.json --manifest data\models\models_manifest.json`
  按预期失败，并写出 `quality_reports/comfyui_smoke_check.json` 与 `quality_reports/real_image_preflight.json`。

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
- ComfyUI 当前只支持 dry-run：写出 `comfyui_dry_run/jobs.json` 和 request preview，不访问本地 ComfyUI。
- `comfyui-smoke-check` 会写出 `quality_reports/comfyui_smoke_check.json`，用于离线确认 workflow、
  模型 manifest、dry-run request preview 和 workflow 引用是否已经具备本地冒烟条件。
- 默认情况下，仍包含 `placeholder` 或 `REVIEW_REQUIRED` 的 ComfyUI 配置会被冒烟检查拦下。
- Seedance 当前只支持 dry-run：写出 `seedance_dry_run/jobs.json` 和 request preview，不访问真实视频服务。
- `build-review-packet` 会汇总剧本、图片、视频、配音和口型任务，生成可人工编辑的审核包。
- `real-image-preflight` 会写出真实图片生成前门禁报告，通过时也只提示停在真实生成前，不调用 ComfyUI。

## 2026-05-03 Phase 2.1 守株待兔视觉方案

- 当前分支：`codex/phase-2-shou-zhu-comedy-10frames`。
- 守株待兔样例已扩展为 10 镜头轻喜剧剧本，输出仍控制在短视频节奏内。
- `scene_02` 明确兔子朝树桩方向跑，`scene_03` 明确兔子撞晕后安全躺在地上，无血腥描写。
- `scene_06` 到 `scene_09` 明确等待动作递进：坐小板凳、趴草席看小虫、躺着打盹、坐起醒悟。
- 等待段同时带季节递进：春末、初夏、夏末、初秋；作物、大树叶色和远山色调随时间变化。
- 分镜提示词已加入固定背景连续性：右后方茅草屋、屋前栅栏水缸、从右下角经过树桩右侧通向房子的田间小径、
  田垄方向和远山轮廓应保持一致。
- 本地预览图目录：`outputs/shou-zhu-dai-tu/real_images_preview_comedy_10/`。
- 该预览目录用于人工视觉审核，不替代正式 `images_raw`、`images_approved` 或未来真实 ComfyUI provider 产物。
- 新增 `register-preview-images <preview_dir> --approved`，可以把人工认可的预览 PNG 复制到
  `images_raw` 和 `images_approved`，重写 `05_video_jobs.json`，并写出 `auto=false` 的图片审核记录。
- 当前守株待兔输出目录已用 `register-preview-images outputs\shou-zhu-dai-tu\real_images_preview_comedy_10 --approved`
  登记 10 张预览图，并重新生成 mock 视频记录。
- 已基于 `images_approved` 生成 10 条 Seedance dry-run 请求预览：
  `outputs/shou-zhu-dai-tu/seedance_dry_run/jobs.json` 和 `outputs/shou-zhu-dai-tu/videos/*.seedance_dry_run.json`。
- `review/review_packet.json` 已刷新，视频审核项包含 Seedance jobs 清单和每个镜头 request preview；
  dry-run artifact paths 已去重，便于人工审核。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe build-video-motion-review outputs\shou-zhu-dai-tu --auto`：
  已生成 10 条视频运动审核项，`review/video_motion_review.json` 中 `approved=10`、`pending=0`。
- 刷新 `review/review_packet.json` 后，视频审核项已包含 `review/video_motion_review.json`。
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe quality-check outputs\shou-zhu-dai-tu`：
  通过，`video_motion_review_schema=passed`、`video_motion_review_files=passed`。

## 2026-05-03 Phase 2.2 视频运动审核

- 当前分支：`codex/phase-2.2-video-motion-review`。
- 新增 `build-video-motion-review outputs\shou-zhu-dai-tu --auto`，用于从
  `seedance_dry_run/jobs.json` 生成 `review/video_motion_review.json`。
- 运动审核文件逐镜记录首帧图片、Seedance request preview、运动提示词、时长、
  背景连续性检查和审核状态。
- 默认不带 `--auto` 时，运动审核项保持 `pending`，便于人工逐镜编辑；带 `--auto`
  只表示离线技术检查通过，不代表真实视频已经生成或通过人工审片。
- `quality-check` 在该文件存在时会校验 schema、状态、首帧路径、request preview 路径、
  背景连续性提示和与 Seedance dry-run jobs 的一致性。
- 已根据独立审核反馈补充反向一致性检查：旧 scene 或重复 scene 混入 `video_motion_review.json`
  时，`quality-check` 会失败并写入 `full_quality.json`。
- `build-review-packet` 会把 `review/video_motion_review.json` 纳入每个视频审核项，
  让统一审核包能够追踪运动提示词审核结果。

## 2026-05-03 Phase 2.3 真实视频生成前门禁

- 当前分支：`codex/phase-2.3-real-video-preflight`。
- 新增 `real-video-preflight outputs\shou-zhu-dai-tu`，用于汇总检查 `05_video_jobs.json`、
  `seedance_dry_run/jobs.json`、`review/video_motion_review.json` 和 `review/review_packet.json`。
- 该命令写出 `quality_reports/real_video_preflight.json`；通过时 `next_step` 为
  `STOP_BEFORE_REAL_VIDEO_GENERATION`，表示必须停在真实 Seedance 调用前等待人工确认。
- `quality-check` 在该报告存在时会校验 schema、`ok` 状态，并在报告曾经通过时重新运行离线视频门禁，
  防止后续改动 Seedance dry-run、运动审核或审核包后继续沿用旧报告。
- 视频门禁会检查 `seedance_dry_run/jobs.json` 与当前 `05_video_jobs.json` 的 scene、source job、
  首帧、prompt、时长和输出路径一致，避免修改视频任务后沿用旧 dry-run。
- 已根据独立审核反馈补齐反向覆盖检查：每个当前视频任务都必须有 Seedance dry-run 覆盖。
- 视频门禁会阻断当前 `05_video_jobs.json` 中重复的 `scene_id` 或 `job_id`，避免同一镜头的新增任务绕过
  dry-run 和审核覆盖。
- `real_video_preflight.json` 会记录当前产物指纹；`quality-check` 会比较保存报告与当前产物指纹，
  防止相关 JSON 和引用文件重新生成后继续沿用旧门禁报告。
- 当前默认 `outputs/shou-zhu-dai-tu` 已重新生成 10 条 Seedance dry-run、运动审核、审核包和
  `quality_reports/real_video_preflight.json`，随后 `quality-check outputs\shou-zhu-dai-tu` 通过。

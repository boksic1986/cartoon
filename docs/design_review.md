# Design Review

## Feasibility

The brief is feasible as a mock-first MVP. The safest first milestone is an
offline pipeline that produces reviewable JSON at each stage, mock image/video
artifacts, subtitles, metadata, and a final fallback media file.

## Conservative Decisions

- Use `04_image_jobs.json` instead of `04_comfyui_jobs.json` so the job format
  remains provider-neutral.
- Let `approve-images --auto` create `05_video_jobs.json`, because video jobs
  should reference approved images rather than raw outputs.
- Keep ComfyUI, Seedance, OpenAI, and real TTS as dry-run or skeleton providers.
- If FFmpeg is unavailable, `compose` writes `final/final_mock.txt` and returns a
  successful command with a clear warning.
- Use conda as the primary documented environment because later GPU and ComfyUI
  work will benefit from environment isolation.

## Dialogue, Voice, And Lip Sync

Dialogue belongs in the script stage. Storyboard scenes assign each narration or
dialogue cue to a scene with estimated timing, speaker, emotion, and mouth
action. The first milestone records simple mouth intent only:
`mouth_action=speaking_simple` and `lip_sync_required=false`.

Precise lip sync is deferred to later providers:

1. `VoiceProvider` creates audio.
2. `AlignmentProvider` creates word, phoneme, or viseme timing.
3. `LipSyncProvider` renders mouth-synced clips.

The MVP should avoid long front-facing speaking shots and use narration-led
storytelling with short character dialogue.

## Risks

- Real ComfyUI workflows may depend on local plugin and model versions.
- Seedance task APIs and polling behavior must be isolated behind provider
  contracts before real integration.
- Exact mouth synchronization requires a separate alignment and lip-sync phase.
- Model and asset licenses need human review before publication.

## Later Phases

1. Connect ComfyUI after local smoke tests.
2. Add Seedance dry-run task polling, then real submission.
3. Add TTS, audio alignment, and optional lip-sync provider.
4. Add batch production only after the single-idiom workflow is stable.

## Current Completion

- Project structure, conda environment file, README, AGENTS, and project
  management docs are present.
- Pydantic schemas cover idiom profiles, scripts, storyboards, image jobs,
  video jobs, speech cues, subtitles, and publish metadata.
- Dialogue and voice text are generated at script stage, then assigned to
  storyboard speech cues with estimated timing.
- Mock image, video, subtitle, compose fallback, cover, and metadata steps run
  without external services.
- `04_image_jobs.json` is provider-neutral, and `05_video_jobs.json` is created
  after image approval.

## Unfinished Work

- Real ComfyUI API calls.
- Real Seedance API calls.
- Real TTS audio, audio alignment, and precise lip sync.
- Batch production and publishing automation.

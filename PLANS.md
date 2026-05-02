# Plans

## MVP Plan

Build a mock-first pipeline that converts one idiom profile JSON into reviewable
intermediate JSON files, mock images, mock videos, subtitles, publish metadata,
and a final mock media artifact.

## Current Milestone: Phase 1.1 Hardening

Completed:

1. Initialize the Python 3.11 project.
2. Define Pydantic schemas for every JSON artifact.
3. Implement deterministic script, storyboard, prompt, provider, subtitle, and
   compose steps.
4. Keep all external providers behind mock or dry-run interfaces.
5. Push the baseline repository to `git@github.com:boksic1986/cartoon.git`.
6. Add single-step CLI flow coverage.
7. Write prompt quality reports during `build-image-prompts`.

Next:

1. Add a dedicated `quality-check` CLI command for already-generated artifacts.
2. Add optional FFmpeg smoke test instructions for machines with FFmpeg.
3. Prepare ComfyUI local smoke-test checklist before real provider work.

## Deferred Milestones

1. Real ComfyUI image provider after local smoke tests.
2. Real Seedance video provider after dry-run task records are stable.
3. Real TTS, audio alignment, and lip-sync provider after script and storyboard
   timing is stable.

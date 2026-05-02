# Plans

## MVP Plan

Build a mock-first pipeline that converts one idiom profile JSON into reviewable
intermediate JSON files, mock images, mock videos, subtitles, publish metadata,
and a final mock media artifact.

## Current Milestone

1. Initialize the Python 3.11 project.
2. Define Pydantic schemas for every JSON artifact.
3. Implement deterministic script, storyboard, prompt, provider, subtitle, and
   compose steps.
4. Keep all external providers behind mock or dry-run interfaces.
5. Run `pytest` and `idiom-video run-all data/idioms/shou-zhu-dai-tu.json --providers mock`.

## Deferred Milestones

1. Real ComfyUI image provider after local smoke tests.
2. Real Seedance video provider after dry-run task records are stable.
3. Real TTS, audio alignment, and lip-sync provider after script and storyboard
   timing is stable.


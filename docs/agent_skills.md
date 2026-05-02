# Agent Skills And Ownership

This project can be implemented by one Codex thread or by multiple agents. Keep
ownership explicit when parallelizing.

## Available Official Plugins

- Superpowers: planning, execution, TDD, verification, and branch finishing.
- Browser Use: later local browser checks for visual review tools or dashboards.
- GitHub: later repository, pull request, issue, and CI workflows.

No extra plugin is required for the mock-first MVP.

## Agent Split

| Agent | Skill Focus | Primary Paths | Permissions |
| --- | --- | --- | --- |
| Agent 1 | schemas, config, CLI foundation | `src/idiom_video/schemas.py`, `config.py`, `cli.py`, `utils/` | May edit core contracts after coordinating with all agents. |
| Agent 2 | script, storyboard, prompt | `script_writer.py`, `storyboard_writer.py`, `prompt_builder.py`, `data/idioms/`, `data/style/` | Owns story text, prompt templates, and speech cue structure. |
| Agent 3 | image providers | `providers/base.py`, `providers/image_mock.py`, `providers/image_comfyui.py`, `workflows/comfyui/` | May add dry-run fields; no real network calls in tests. |
| Agent 4 | video, TTS, subtitles, compose | `providers/video_mock.py`, `providers/video_seedance.py`, `providers/tts_mock.py`, `media/` | Owns fallback behavior when FFmpeg or real providers are absent. |
| Agent 5 | quality and review | `quality_rules.py`, `docs/review_checklist.md`, `data/models/` | Owns copyright, age-suitability, and model license checks. |
| Agent 6 | docs and verification | `README.md`, `AGENTS.md`, `PLANS.md`, `CURRENT_STATUS.md`, `REPO_MAP.md`, `tests/` | Owns test commands, onboarding, and final verification notes. |

## Collaboration Rules

- Do not revert another agent's changes.
- Keep generated outputs under `outputs/{idiom_slug}/`.
- Keep tests offline and mock-only.
- Keep examples focused on AI animation production; do not add unrelated
  technical prompts outside this domain.
- Real API keys must never be placed in code, docs, logs, tests, or examples.

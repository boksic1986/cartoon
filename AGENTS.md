# Agent Rules

## Project Scope

This repository builds an AI animation production pipeline for Chinese idiom
story videos. Keep all examples focused on animation, media generation, review,
and publishing metadata. Do not add unrelated technical prompts, tooling, or
examples outside this domain.

## Engineering Rules

- Use Python 3.11+.
- Use Pydantic for every core JSON artifact.
- Use Typer for CLI commands.
- Use pytest for tests.
- Keep all external services behind provider interfaces.
- Every provider must support mock or dry-run behavior.
- Tests must not call real external services.
- Never commit or print real API keys.
- Keep paths Windows-compatible; prefer `pathlib.Path`.
- Every intermediate artifact must be JSON and reviewable.

## Content And Copyright Rules

- Do not request or imitate specific copyrighted characters.
- Do not request celebrity faces, public figure likenesses, or real-person
  portraits.
- Do not imitate a specific living artist.
- Keep visuals child-friendly and suitable for educational animation.
- Do not rely on unreviewed LoRA, model, or asset licenses for publishing.

## Multi-Agent Boundaries

When using multiple agents, keep file ownership explicit:

- Agent 1: schemas, config, CLI foundation, utils.
- Agent 2: script writer, storyboard writer, prompt builder, idiom/style data.
- Agent 3: image provider base, mock image provider, ComfyUI dry-run skeleton.
- Agent 4: video provider, TTS mock, subtitles, compose, metadata.
- Agent 5: quality rules, forbidden terms, review checklist, model manifest.
- Agent 6: README, project management docs, tests, final verification.

Agents should not revert changes made by other agents. If a file has mixed
ownership, coordinate before editing it.

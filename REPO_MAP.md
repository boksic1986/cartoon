# Repo Map

## Root

- `README.md`: install and usage guide.
- `AGENTS.md`: rules for Codex agents and human contributors.
- `PLANS.md`: project roadmap and current milestone.
- `CURRENT_STATUS.md`: current execution status and verification commands.
- `REPO_MAP.md`: high-level directory map.
- `pyproject.toml`: Python package metadata and CLI entry point.
- `environment.yml`: conda environment definition.
- `outputs/`: generated local artifacts. This directory is produced by the CLI.

## Source

- `src/idiom_video/schemas.py`: Pydantic contracts for all JSON artifacts.
- `src/idiom_video/config.py`: environment-backed settings.
- `src/idiom_video/cli.py`: Typer CLI.
- `src/idiom_video/script_writer.py`: idiom profile to script.
- `src/idiom_video/storyboard_writer.py`: script to storyboard.
- `src/idiom_video/prompt_builder.py`: storyboard to prompts and image jobs.
- `src/idiom_video/quality_rules.py`: validation and review gates.
- `src/idiom_video/providers/`: mock and dry-run provider interfaces.
- `src/idiom_video/media/`: subtitles, composition, cover, metadata.
- `src/idiom_video/utils/`: path, JSON, logging, retry helpers.

## Data And Workflows

- `data/idioms/`: source idiom profile JSON files.
- `data/style/`: style bible, negative prompt, forbidden terms.
- `data/models/`: model license manifest.
- `workflows/comfyui/`: placeholder workflow references for later real ComfyUI work.
- `docs/agent_skills.md`: multi-agent split, skill usage, and file permissions.

## Tests

- `tests/`: unit and integration tests. Tests must remain offline and mock-only.

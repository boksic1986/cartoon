# Current Status

Status: Phase 1.1 hardening in progress.

## Git

- Branch: `main`
- Remote: `git@github.com:boksic1986/cartoon.git`
- Latest pushed baseline: `f524fe9 chore: initialize mock idiom video pipeline`

## Environment

- Conda is expected at `D:\ProgramData\miniconda3`.
- Recommended environment name: `idiom-video`.
- Python version: 3.11.
- Pip index: Tsinghua PyPI mirror.
- Conda channels: Tsinghua defaults and cloud mirrors.

## Active Constraints

- Mock mode must run without network calls.
- Tests must not call external services.
- Real API keys must never appear in code, docs, tests, logs, or sample output.
- This project is only for AI animation production workflows and should keep
  prompts, procedures, and tooling focused on that domain.

## Next Verification

Run:

```powershell
D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest
D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock
```

Latest verification:

- `D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`: 17 passed.
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock`: generated the expected `outputs/shou-zhu-dai-tu/` artifacts.
- `outputs/shou-zhu-dai-tu/quality_reports/prompt_quality.json`: `ok=true`, no issues.

Current hardening changes:

- `build-image-prompts` now writes `quality_reports/prompt_quality.json`.
- Positive image prompts are blocked if they contain forbidden terms.
- The single-step CLI flow is covered by integration tests.

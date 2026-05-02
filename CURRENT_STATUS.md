# Current Status

Status: MVP mock flow implemented and verified locally.

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

- `D:\ProgramData\miniconda3\envs\idiom-video\python.exe -m pytest`: 15 passed.
- `D:\ProgramData\miniconda3\envs\idiom-video\Scripts\idiom-video.exe run-all data\idioms\shou-zhu-dai-tu.json --providers mock`: generated the expected `outputs/shou-zhu-dai-tu/` artifacts.

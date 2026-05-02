from __future__ import annotations

from pathlib import Path


class TTSMockProvider:
    provider_name = "mock"

    def synthesize(self, text: str, output_path: str) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"Mock TTS manifest only.\ntext={text}\n", encoding="utf-8")
        return str(output)

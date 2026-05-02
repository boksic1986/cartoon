from __future__ import annotations

from pydantic import BaseModel


class QualityIssue(BaseModel):
    message: str
    term: str | None = None
    path: str | None = None


class QualityResult(BaseModel):
    ok: bool
    issues: list[QualityIssue] = []


def check_forbidden_terms(text: str, forbidden_terms: list[str]) -> QualityResult:
    issues = [
        QualityIssue(message=f"forbidden term found: {term}", term=term)
        for term in forbidden_terms
        if term and term in text
    ]
    return QualityResult(ok=not issues, issues=issues)


def validate_models_manifest(manifest: dict) -> QualityResult:
    issues: list[QualityIssue] = []
    for index, model in enumerate(manifest.get("models", [])):
        for field in ["name", "type", "license"]:
            if field not in model:
                issues.append(QualityIssue(message=f"model entry missing {field}", path=f"models[{index}]"))
        if "commercial_use_allowed" not in model:
            issues.append(QualityIssue(message="model entry missing commercial_use_allowed", path=f"models[{index}]"))
    return QualityResult(ok=not issues, issues=issues)

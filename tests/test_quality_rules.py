from idiom_video.quality_rules import check_forbidden_terms, validate_models_manifest


def test_check_forbidden_terms_finds_blocked_word():
    result = check_forbidden_terms("请画一个明星脸角色", ["明星脸"])

    assert not result.ok
    assert result.issues[0].term == "明星脸"


def test_models_manifest_requires_license():
    manifest = {"models": [{"name": "example", "type": "checkpoint"}]}
    result = validate_models_manifest(manifest)

    assert not result.ok
    assert "license" in result.issues[0].message

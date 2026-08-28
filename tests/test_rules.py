from labelguard.rules.distilled_spirits import (
    identify_review_requirements,
    required_field_status,
    validate_distilled_spirits_structure,
)


def _field(
    name,
    decision,
    confidence=0.95,
):
    return {
        "field": name,
        "decision": decision,
        "confidence": confidence,
    }


def test_required_field_status():
    results = [
        _field("brand_name", "MATCH"),
        _field("class_type", "MATCH"),
        _field("abv", "MATCH"),
        _field("net_contents", "MATCH"),
        _field("name_address", "MATCH"),
        _field("government_warning", "NEEDS_REVIEW"),
    ]

    status = required_field_status(
        results
    )

    assert status["brand_name"] == "MATCH"
    assert status["government_warning"] == "NEEDS_REVIEW"


def test_identify_review_requirements():
    results = [
        _field(
            "brand_name",
            "MATCH",
            0.95,
        ),
        _field(
            "abv",
            "NEEDS_REVIEW",
            0.61,
        ),
    ]

    requirements = identify_review_requirements(
        results
    )

    assert any(
        "abv" in item
        for item in requirements
    )


def test_structural_result_pass():
    results = [
        _field("brand_name", "MATCH"),
        _field("class_type", "MATCH"),
        _field("abv", "MATCH"),
        _field("net_contents", "MATCH"),
        _field("name_address", "MATCH"),
        _field("government_warning", "MATCH"),
    ]

    result = validate_distilled_spirits_structure(
        results
    )

    assert result["structural_result"] == "PASS"


def test_structural_result_mismatch():
    results = [
        _field("brand_name", "MISMATCH"),
        _field("class_type", "MATCH"),
        _field("abv", "MATCH"),
        _field("net_contents", "MATCH"),
        _field("name_address", "MATCH"),
        _field("government_warning", "MATCH"),
    ]

    result = validate_distilled_spirits_structure(
        results
    )

    assert result["structural_result"] == "MISMATCH"


def test_structural_result_needs_review():
    results = [
        _field("brand_name", "MATCH"),
        _field("class_type", "MATCH"),
        _field("abv", "MATCH"),
        _field("net_contents", "MATCH"),
        _field("name_address", "MATCH"),
        _field(
            "government_warning",
            "NEEDS_REVIEW",
        ),
    ]

    result = validate_distilled_spirits_structure(
        results
    )

    assert result["structural_result"] == "NEEDS_REVIEW"


def test_missing_field_requires_review():
    results = [
        _field("brand_name", "MATCH"),
        _field("class_type", "MATCH"),
    ]

    result = validate_distilled_spirits_structure(
        results
    )

    assert result["structural_result"] == "NEEDS_REVIEW"
    assert "abv" in result["missing_or_uncertain"]

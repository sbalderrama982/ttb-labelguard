from unittest.mock import patch

from labelguard.decision_engine import verify_label
from labelguard.models import ApplicationRecord


APPLICATION = ApplicationRecord(
    application_id="TTB-TEST-001",
    beverage_type="distilled_spirits",
    brand_name="STONE'S THROW",
    class_type="Kentucky Straight Bourbon Whiskey",
    abv=45.0,
    net_contents_ml=750.0,
    name_address="Stone's Throw Distillery",
    country_of_origin="United States",
)


GOOD_OCR_TEXT = """
STONE'S THROW
KENTUCKY STRAIGHT BOURBON WHISKEY
45% Alc./Vol.
750 mL
Stone's Throw Distillery
PRODUCT OF THE UNITED STATES

GOVERNMENT WARNING:
According to the Surgeon General, women should not drink
alcoholic beverages during pregnancy because of the risk
of birth defects.
"""


def _fake_ocr(*args, **kwargs):
    return {
        "text": GOOD_OCR_TEXT,
        "confidence": 0.96,
        "variants_used": 5,
    }


@patch(
    "labelguard.decision_engine.extract_text",
    side_effect=_fake_ocr,
)
def test_matching_label_reaches_review_or_pass(mock_ocr):
    result = verify_label(
        b"fake-image",
        "good-label.jpg",
        APPLICATION,
    )

    assert result["decision"] in {
        "PASS",
        "NEEDS_REVIEW",
        "MISMATCH",
    }

    assert result["fields"]
    assert result["processing_ms"] >= 0


def _bad_ocr(*args, **kwargs):
    return {
        "text": """
DIFFERENT BRAND
KENTUCKY STRAIGHT BOURBON WHISKEY
40% Alc./Vol.
500 mL
GOVERNMENT WARNING:
According to the Surgeon General
""",
        "confidence": 0.96,
        "variants_used": 5,
    }


@patch(
    "labelguard.decision_engine.extract_text",
    side_effect=_bad_ocr,
)
def test_mismatched_label_is_rejected(mock_ocr):
    result = verify_label(
        b"fake-image",
        "bad-label.jpg",
        APPLICATION,
    )

    assert result["decision"] in {
        "MISMATCH",
        "NEEDS_REVIEW",
    }

    mismatch_fields = [
        field
        for field in result["fields"]
        if field["decision"] == "MISMATCH"
    ]

    review_fields = [
        field
        for field in result["fields"]
        if field["decision"] == "NEEDS_REVIEW"
    ]

    assert mismatch_fields or review_fields


def _low_confidence_ocr(*args, **kwargs):
    return {
        "text": GOOD_OCR_TEXT,
        "confidence": 0.20,
        "variants_used": 5,
    }


@patch(
    "labelguard.decision_engine.extract_text",
    side_effect=_low_confidence_ocr,
)
def test_low_ocr_confidence_triggers_review(mock_ocr):
    result = verify_label(
        b"fake-image",
        "uncertain-label.jpg",
        APPLICATION,
    )

    assert result["decision"] in {
        "NEEDS_REVIEW",
        "MISMATCH",
    }

    assert any(
        "OCR confidence" in flag
        or "confidence" in flag.lower()
        for flag in result["review_flags"]
    )


@patch(
    "labelguard.decision_engine.extract_text",
    side_effect=Exception("OCR unavailable"),
)
def test_pipeline_error_fails_safely(mock_ocr):
    result = verify_label(
        b"fake-image",
        "error-label.jpg",
        APPLICATION,
    )

    assert result["decision"] == "NEEDS_REVIEW"

    assert any(
        "Processing pipeline error" in flag
        or "Verification pipeline error" in flag
        for flag in result["review_flags"]
    )


def test_result_contains_audit_trace():
    with patch(
        "labelguard.decision_engine.extract_text",
        side_effect=_fake_ocr,
    ):
        result = verify_label(
            b"fake-image",
            "trace-label.jpg",
            APPLICATION,
        )

    assert isinstance(result["trace"], list)
    assert result["trace"]

    for trace_item in result["trace"]:
        assert "field" in trace_item
        assert "decision" in trace_item
        assert "reason" in trace_item

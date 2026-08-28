import time
from typing import Dict, List, Optional

from labelguard.extraction import extract_fields
from labelguard.models import (
    ApplicationRecord,
    ExtractedField,
    FieldResult,
)
from labelguard.normalization import (
    compare_brand,
    compare_percentage,
    compare_text,
    compare_volume,
)
from labelguard.ocr import extract_text


MIN_OCR_CONFIDENCE = 0.55
REVIEW_CONFIDENCE = 0.70


def _field_value(
    fields: List[ExtractedField],
    name: str,
) -> Optional[ExtractedField]:
    """
    Locate one extracted field.
    """

    for field in fields:
        if field.field == name:
            return field

    return None


def _text_result(
    field_name: str,
    expected: Optional[str],
    observed: Optional[str],
    confidence: float,
) -> FieldResult:
    """
    Compare textual application fields.
    """

    if not observed:
        return FieldResult(
            field=field_name,
            application=expected,
            observed=None,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="The required value was not confidently detected on the label.",
            evidence="No usable OCR evidence was extracted.",
        )

    matched = compare_text(
        expected,
        observed,
    )

    if matched:
        return FieldResult(
            field=field_name,
            application=expected,
            observed=observed,
            decision="MATCH",
            confidence=confidence,
            reason="The observed value matches the application after controlled normalization.",
            evidence=observed,
        )

    return FieldResult(
        field=field_name,
        application=expected,
        observed=observed,
        decision="MISMATCH",
        confidence=confidence,
        reason="The observed value does not match the application value.",
        evidence=observed,
    )


def _brand_result(
    expected: Optional[str],
    observed: Optional[str],
    confidence: float,
) -> FieldResult:
    """
    Compare brand names using punctuation- and
    capitalization-tolerant normalization.
    """

    if not observed:
        return FieldResult(
            field="brand_name",
            application=expected,
            observed=None,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="No sufficiently reliable brand evidence was extracted.",
            evidence="",
        )

    matched = compare_brand(
        expected,
        observed,
    )

    if matched:
        return FieldResult(
            field="brand_name",
            application=expected,
            observed=observed,
            decision="MATCH",
            confidence=confidence,
            reason=(
                "Brand names match after controlled normalization "
                "of capitalization and punctuation."
            ),
            evidence=observed,
        )

    return FieldResult(
        field="brand_name",
        application=expected,
        observed=observed,
        decision="MISMATCH",
        confidence=confidence,
        reason="The observed brand does not match the application record.",
        evidence=observed,
    )


def _abv_result(
    expected: Optional[float],
    observed: Optional[str],
    confidence: float,
) -> FieldResult:
    """
    Compare alcohol-by-volume values.
    """

    if expected is None:
        return FieldResult(
            field="abv",
            application=None,
            observed=observed,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="No application ABV was supplied.",
            evidence=observed or "",
        )

    if not observed:
        return FieldResult(
            field="abv",
            application=f"{expected:g}%",
            observed=None,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="No reliable ABV value was detected.",
            evidence="",
        )

    matched = compare_percentage(
        expected,
        observed,
    )

    if matched:
        return FieldResult(
            field="abv",
            application=f"{expected:g}%",
            observed=observed,
            decision="MATCH",
            confidence=confidence,
            reason="Observed ABV matches the application value.",
            evidence=observed,
        )

    return FieldResult(
        field="abv",
        application=f"{expected:g}%",
        observed=observed,
        decision="MISMATCH",
        confidence=confidence,
        reason="Observed ABV differs from the application value.",
        evidence=observed,
    )


def _volume_result(
    expected: Optional[float],
    observed: Optional[str],
    confidence: float,
) -> FieldResult:
    """
    Compare net contents after unit normalization.
    """

    if expected is None:
        return FieldResult(
            field="net_contents",
            application=None,
            observed=observed,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="No application net-content value was supplied.",
            evidence=observed or "",
        )

    if not observed:
        return FieldResult(
            field="net_contents",
            application=f"{expected:g} mL",
            observed=None,
            decision="NEEDS_REVIEW",
            confidence=confidence,
            reason="No reliable net-content value was detected.",
            evidence="",
        )

    matched = compare_volume(
        expected,
        observed,
    )

    if matched:
        return FieldResult(
            field="net_contents",
            application=f"{expected:g} mL",
            observed=observed,
            decision="MATCH",
            confidence=confidence,
            reason="Observed net contents match after unit normalization.",
            evidence=observed,
        )

    return FieldResult(
        field="net_contents",
        application=f"{expected:g} mL",
        observed=observed,
        decision="MISMATCH",
        confidence=confidence,
        reason="Observed net contents differ from the application value.",
        evidence=observed,
    )


def _warning_result(
    observed: Optional[str],
    confidence: float,
) -> FieldResult:
    """
    Evaluate the government warning.

    Important design decision:
    OCR presence does not automatically prove visual typography.
    Therefore the field can pass textual checks while still
    generating a human-review flag.
    """

    if not observed:
        return FieldResult(
            field="government_warning",
            application="Required government warning",
            observed=None,
            decision="MISMATCH",
            confidence=confidence,
            reason="The required government warning was not detected.",
            evidence="",
        )

    upper = observed.upper()

    required_phrases = [
        "GOVERNMENT WARNING:",
        "SURGEON GENERAL",
        "DRINKING ALCOHOLIC BEVERAGES",
    ]

    missing = [
        phrase
        for phrase in required_phrases
        if phrase not in upper
    ]

    if missing:
        return FieldResult(
            field="government_warning",
            application="Required government warning",
            observed=observed,
            decision="MISMATCH",
            confidence=confidence,
            reason=(
                "The detected warning is missing one or more "
                "expected textual components."
            ),
            evidence=observed,
        )

    return FieldResult(
        field="government_warning",
        application="Required government warning",
        observed=observed,
        decision="NEEDS_REVIEW",
        confidence=confidence,
        reason=(
            "Required warning text was detected. Human review is "
            "required to verify typography, placement, and other "
            "visual requirements."
        ),
        evidence=observed,
    )


def _build_trace(
    field_results: List[FieldResult],
) -> List[Dict[str, object]]:
    """
    Build a machine-readable decision trace.
    """

    trace = []

    for result in field_results:
        trace.append(
            {
                "field": result.field,
                "decision": result.decision,
                "confidence": round(
                    result.confidence,
                    4,
                ),
                "application_value": result.application,
                "observed_value": result.observed,
                "reason": result.reason,
                "evidence": result.evidence,
            }
        )

    return trace


def verify_label(
    image_bytes: bytes,
    filename: str,
    application: ApplicationRecord,
) -> Dict[str, object]:
    """
    Main verification pipeline.

    Pipeline:
        image
          ↓
        local OCR
          ↓
        structured extraction
          ↓
        normalized comparison
          ↓
        rule evaluation
          ↓
        human-review gate

    The system never treats uncertain OCR as a confident approval.
    """

    start = time.perf_counter()

    review_flags: List[str] = []

    try:
        ocr_result = extract_text(
            image_bytes
        )

        extracted_text = str(
            ocr_result.get("text", "")
        )

        ocr_confidence = float(
            ocr_result.get(
                "confidence",
                0.0,
            )
        )

        if ocr_confidence < MIN_OCR_CONFIDENCE:
            review_flags.append(
                "Overall OCR confidence is below the automatic-review threshold."
            )

        fields = extract_fields(
            extracted_text,
            ocr_confidence,
        )

        brand = _field_value(
            fields,
            "brand_name",
        )

        class_type = _field_value(
            fields,
            "class_type",
        )

        abv = _field_value(
            fields,
            "abv",
        )

        net_contents = _field_value(
            fields,
            "net_contents",
        )

        name_address = _field_value(
            fields,
            "name_address",
        )

        country = _field_value(
            fields,
            "country_of_origin",
        )

        warning = _field_value(
            fields,
            "government_warning",
        )

        results = [
            _brand_result(
                application.brand_name,
                brand.value if brand else None,
                brand.confidence if brand else ocr_confidence,
            ),
            _text_result(
                "class_type",
                application.class_type,
                class_type.value if class_type else None,
                class_type.confidence if class_type else ocr_confidence,
            ),
            _abv_result(
                application.abv,
                abv.value if abv else None,
                abv.confidence if abv else ocr_confidence,
            ),
            _volume_result(
                application.net_contents_ml,
                net_contents.value if net_contents else None,
                net_contents.confidence if net_contents else ocr_confidence,
            ),
            _text_result(
                "name_address",
                application.name_address,
                name_address.value if name_address else None,
                name_address.confidence if name_address else ocr_confidence,
            ),
        ]

        if application.country_of_origin:
            results.append(
                _text_result(
                    "country_of_origin",
                    application.country_of_origin,
                    country.value if country else None,
                    country.confidence if country else ocr_confidence,
                )
            )

        warning_result = _warning_result(
            warning.value if warning else None,
            warning.confidence if warning else ocr_confidence,
        )

        results.append(
            warning_result
        )

        # Any mismatch is a hard stop.
        if any(
            result.decision == "MISMATCH"
            for result in results
        ):
            decision = "MISMATCH"

        # Anything needing human review prevents an automatic pass.
        elif any(
            result.decision == "NEEDS_REVIEW"
            for result in results
        ):
            decision = "NEEDS_REVIEW"

        else:
            decision = "PASS"

        if warning_result.decision == "NEEDS_REVIEW":
            review_flags.append(
                "Human verification required for government-warning typography and visual presentation."
            )

        if ocr_confidence < REVIEW_CONFIDENCE:
            review_flags.append(
                "OCR confidence is below the preferred confidence level for unattended verification."
            )

        trace = _build_trace(
            results
        )

    except Exception as exc:
        decision = "NEEDS_REVIEW"
        extracted_text = ""
        ocr_confidence = 0.0
        results = []
        trace = []

        review_flags.append(
            f"Verification pipeline error: {exc}"
        )

    processing_ms = int(
        (time.perf_counter() - start)
        * 1000
    )

    return {
        "filename": filename,
        "decision": decision,
        "processing_ms": processing_ms,
        "ocr_confidence": ocr_confidence,
        "fields": [
            {
                "field": result.field,
                "application": result.application,
                "observed": result.observed,
                "decision": result.decision,
                "confidence": result.confidence,
                "reason": result.reason,
                "evidence": result.evidence,
            }
            for result in results
        ],
        "review_flags": review_flags,
        "extracted_text": extracted_text,
        "trace": trace,
    }

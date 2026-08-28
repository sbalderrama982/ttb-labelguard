from datetime import datetime, timezone
from typing import Any, Dict, List


def create_evidence_record(
    application_id: str,
    filename: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create an audit-friendly evidence record.

    The record captures:
    - when verification occurred
    - which application was evaluated
    - which image was evaluated
    - overall decision
    - field-level decisions
    - OCR confidence
    - human-review flags

    This prototype does not persist records to an external
    database. The function simply creates a structured record
    that could later be stored by an authorized system.
    """

    return {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "application_id": application_id,

        "source_file": filename,

        "decision": result.get(
            "decision",
            "NEEDS_REVIEW",
        ),

        "processing_ms": result.get(
            "processing_ms",
            0,
        ),

        "ocr_confidence": result.get(
            "ocr_confidence",
            0.0,
        ),

        "field_results": result.get(
            "fields",
            [],
        ),

        "review_flags": result.get(
            "review_flags",
            [],
        ),

        "decision_trace": result.get(
            "trace",
            [],
        ),
    }


def summarize_evidence(
    result: Dict[str, Any],
) -> List[str]:
    """
    Produce concise explanations suitable for an agent.
    """

    messages = []

    decision = result.get(
        "decision",
        "NEEDS_REVIEW",
    )

    if decision == "PASS":
        messages.append(
            "All automatically evaluated fields matched "
            "the supplied application data."
        )

    elif decision == "MISMATCH":
        messages.append(
            "One or more label fields did not match "
            "the supplied application data."
        )

    else:
        messages.append(
            "The system could not establish sufficient "
            "evidence for an automatic pass."
        )

    for field in result.get(
        "fields",
        [],
    ):
        field_name = field.get(
            "field",
            "unknown",
        )

        field_decision = field.get(
            "decision",
            "NEEDS_REVIEW",
        )

        reason = field.get(
            "reason",
            "",
        )

        if field_decision == "MISMATCH":
            messages.append(
                f"{field_name}: mismatch — {reason}"
            )

        elif field_decision == "NEEDS_REVIEW":
            messages.append(
                f"{field_name}: human review — {reason}"
            )

    for flag in result.get(
        "review_flags",
        [],
    ):
        messages.append(
            f"Review flag: {flag}"
        )

    return messages


def exportable_record(
    application_id: str,
    filename: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return a clean record suitable for future API/database
    integration or JSON export.
    """

    evidence = create_evidence_record(
        application_id=application_id,
        filename=filename,
        result=result,
    )

    evidence["summary"] = summarize_evidence(
        result
    )

    return evidence

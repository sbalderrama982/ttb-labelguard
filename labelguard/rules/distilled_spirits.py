from typing import Dict, List


REQUIRED_FIELDS = [
    "brand_name",
    "class_type",
    "abv",
    "net_contents",
    "name_address",
    "government_warning",
]


def required_field_status(
    field_results: List[Dict[str, object]],
) -> Dict[str, str]:
    """
    Create a simple status map for required label elements.

    This rule layer intentionally does not make the final
    compliance determination. It identifies which elements
    require attention so the decision engine can combine
    evidence with human-review requirements.
    """

    status = {
        field: "NOT_EVALUATED"
        for field in REQUIRED_FIELDS
    }

    for result in field_results:
        field_name = str(
            result.get("field", "")
        )

        if field_name not in status:
            continue

        decision = str(
            result.get(
                "decision",
                "NEEDS_REVIEW",
            )
        )

        if decision == "MATCH":
            status[field_name] = "MATCH"

        elif decision == "MISMATCH":
            status[field_name] = "MISMATCH"

        else:
            status[field_name] = "NEEDS_REVIEW"

    return status


def identify_review_requirements(
    field_results: List[Dict[str, object]],
) -> List[str]:
    """
    Identify conditions that should be escalated to an agent.

    The prototype deliberately uses a conservative approach:
    uncertainty becomes review rather than automatic approval.
    """

    requirements = []

    for result in field_results:
        field_name = str(
            result.get("field", "")
        )

        decision = str(
            result.get(
                "decision",
                "NEEDS_REVIEW",
            )
        )

        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )

        if decision == "NEEDS_REVIEW":
            requirements.append(
                f"{field_name} requires human verification."
            )

        if confidence < 0.70:
            requirements.append(
                f"{field_name} has confidence below 70%."
            )

    return requirements


def validate_distilled_spirits_structure(
    field_results: List[Dict[str, object]],
) -> Dict[str, object]:
    """
    Evaluate structural completeness for a distilled-spirit
    label verification request.

    Returns evidence for downstream decision-making rather
    than making a legal determination.
    """

    status = required_field_status(
        field_results
    )

    review_requirements = identify_review_requirements(
        field_results
    )

    mismatches = [
        field
        for field, value in status.items()
        if value == "MISMATCH"
    ]

    missing_or_uncertain = [
        field
        for field, value in status.items()
        if value in (
            "NOT_EVALUATED",
            "NEEDS_REVIEW",
        )
    ]

    if mismatches:
        overall = "MISMATCH"

    elif missing_or_uncertain:
        overall = "NEEDS_REVIEW"

    else:
        overall = "PASS"

    return {
        "beverage_type": "distilled_spirits",
        "required_fields": REQUIRED_FIELDS,
        "field_status": status,
        "mismatches": mismatches,
        "missing_or_uncertain": missing_or_uncertain,
        "review_requirements": review_requirements,
        "structural_result": overall,
    }

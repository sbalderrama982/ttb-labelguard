import re

from labelguard.models import ExtractedField


def extract_abv(text: str) -> str:
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*%",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return match.group(1)


def extract_net_contents(text: str) -> str:
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(mL|ML|L|LITERS?|LITRES?)\b",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    value = match.group(1)
    unit = match.group(2)

    if unit.lower() == "ml":
        unit = "mL"
    else:
        unit = "L"

    return f"{value} {unit}"


def extract_class_type(text: str) -> str:
    patterns = [
        r"\b(KENTUCKY\s+STRAIGHT\s+BOURBON\s+WHISKEY)\b",
        r"\b(STRAIGHT\s+BOURBON\s+WHISKEY)\b",
        r"\b(BOURBON\s+WHISKEY)\b",
        r"\b(RYE\s+WHISKEY)\b",
        r"\b(VODKA)\b",
        r"\b(GIN)\b",
        r"\b(RUM)\b",
        r"\b(TEQUILA)\b",
        r"\b(BRANDY)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return " ".join(
                match.group(1).split()
            ).title()

    return ""


def extract_country(text: str) -> str:
    patterns = [
        r"\bPRODUCT\s+OF\s+THE\s+UNITED\s+STATES\b",
        r"\bPRODUCT\s+OF\s+UNITED\s+STATES\b",
        r"\bMADE\s+IN\s+THE\s+UNITED\s+STATES\b",
        r"\bMADE\s+IN\s+UNITED\s+STATES\b",
    ]

    for pattern in patterns:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return "UNITED STATES"

    return ""


def extract_warning(text: str) -> str:
    match = re.search(
        r"(GOVERNMENT\s+WARNING\s*:?.*)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).strip()


def extract_brand_name(text: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    for line in lines:
        upper = line.upper()

        if upper.startswith("PRODUCT OF"):
            continue

        if upper.startswith("MADE IN"):
            continue

        if upper.startswith("GOVERNMENT WARNING"):
            continue

        if "%" in line:
            continue

        if re.search(
            r"\b(WHISKEY|WHISKY|BOURBON|VODKA|GIN|RUM|TEQUILA|BRANDY)\b",
            upper,
        ):
            continue

        return line

    return ""


def extract_name_address(text: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:
        upper = line.upper()

        if any(
            marker in upper
            for marker in (
                "DISTILLERY",
                "DISTILLER",
                "BREWERY",
                "VINEYARD",
                "WINERY",
            )
        ):
            return line

    return ""


def extract_fields(
    text: str,
    ocr_confidence: float = 1.0,
) -> list[ExtractedField]:

    confidence = max(
        0.0,
        min(
            1.0,
            float(ocr_confidence),
        ),
    )

    values = {
        "brand_name": extract_brand_name(text),
        "class_type": extract_class_type(text),
        "abv": extract_abv(text),
        "net_contents": extract_net_contents(text),
        "name_address": extract_name_address(text),
        "country_of_origin": extract_country(text),
        "government_warning": extract_warning(text),
    }

    extracted = []

    for field_name, value in values.items():
        if value:
            extracted.append(
                ExtractedField(
                    field=field_name,
                    value=value,
                    confidence=confidence,
                    evidence=value,
                )
            )

    return extracted

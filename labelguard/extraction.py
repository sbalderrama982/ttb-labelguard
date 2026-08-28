import re
from typing import Dict, List

from labelguard.models import ExtractedField


WARNING_PHRASE = (
    "GOVERNMENT WARNING:"
)


def _find_match(
    pattern: str,
    text: str,
    flags: int = re.IGNORECASE,
) -> str:
    """
    Return the first regex capture group found in text.
    """

    match = re.search(
        pattern,
        text,
        flags,
    )

    if not match:
        return ""

    return match.group(1).strip()


def extract_abv(text: str) -> str:
    """
    Extract alcohol-by-volume information.

    Handles common forms such as:
        45%
        45 % Alc./Vol.
        45% ALC/VOL
        Alcohol 45% by volume
    """

    patterns = [
        r"(\d+(?:\.\d+)?)\s*%\s*(?:ALC\.?\s*/?\s*VOL\.?|ALCOHOL\s+BY\s+VOLUME)?",
        r"ALCOHOL\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%",
    ]

    for pattern in patterns:
        value = _find_match(pattern, text)

        if value:
            return value

    return ""


def extract_net_contents(text: str) -> str:
    """
    Extract common metric net-content expressions.
    """

    patterns = [
        r"(\d+(?:\.\d+)?)\s*(ML|M[Ll]|L|LITERS?|LITRES?)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            number = match.group(1)
            unit = match.group(2).lower()

            if unit.startswith("l"):
                return f"{number} L"

            return f"{number} mL"

    return ""


def extract_warning(text: str) -> str:
    """
    Locate the federal government warning text.

    The prototype intentionally separates:
      1. textual presence
      2. exact wording
      3. visual typography

    OCR can provide evidence for the first two but cannot
    reliably establish every typography requirement.
    """

    upper = text.upper()

    start = upper.find(
        WARNING_PHRASE
    )

    if start == -1:
        return ""

    warning = text[start:].strip()

    return warning


def extract_brand_name(text: str) -> str:
    """
    Use simple heuristics to identify a likely brand name.

    The final comparison against the application record is
    intentionally handled by the decision engine.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        # OCR may return a single line.
        words = text.split()

        return " ".join(words[:5])

    # Prefer a prominent early line that is not obviously
    # regulatory or numeric information.
    for line in lines[:8]:
        upper = line.upper()

        if "GOVERNMENT WARNING" in upper:
            continue

        if re.search(
            r"\d+\s*%",
            line,
        ):
            continue

        if len(line) >= 3:
            return line

    return lines[0]


def extract_class_type(
    text: str,
) -> str:
    """
    Identify common distilled-spirit class/type terms.
    """

    candidates = [
        "Kentucky Straight Bourbon Whiskey",
        "Straight Bourbon Whiskey",
        "Bourbon Whiskey",
        "Tennessee Whiskey",
        "Straight Whiskey",
        "Blended Whiskey",
        "American Whiskey",
        "Whiskey",
        "Whisky",
        "Vodka",
        "Gin",
        "Rum",
        "Tequila",
        "Brandy",
        "Cognac",
    ]

    upper = text.upper()

    for candidate in candidates:
        if candidate.upper() in upper:
            return candidate

    return ""


def extract_name_address(
    text: str,
) -> str:
    """
    Extract a likely producer/bottler line.

    This is deliberately conservative because OCR alone
    should not invent a business identity.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    address_terms = [
        "DISTILLERY",
        "DISTILLER",
        "BREWING",
        "BREWER",
        "VINEYARDS",
        "WINERY",
        "COMPANY",
        "CO.",
        "LLC",
        "INC.",
        "ROAD",
        "RD.",
        "STREET",
        "ST.",
        "AVENUE",
        "AVE.",
    ]

    for line in lines:
        upper = line.upper()

        if any(
            term in upper
            for term in address_terms
        ):
            return line

    return ""


def extract_country(
    text: str,
) -> str:
    """
    Identify an explicitly printed country of origin.
    """

    patterns = [
        r"PRODUCT\s+OF\s+([A-Za-z][A-Za-z\s]+)",
        r"MADE\s+IN\s+([A-Za-z][A-Za-z\s]+)",
        r"PRODUCT\s+OF\s+THE\s+([A-Za-z][A-Za-z\s]+)",
    ]

    for pattern in patterns:
        value = _find_match(
            pattern,
            text,
        )

        if value:
            return value.strip(" .,")

    return ""


def extract_fields(
    text: str,
    ocr_confidence: float,
) -> List[ExtractedField]:
    """
    Extract all supported label fields.

    Confidence is intentionally derived conservatively from
    the underlying OCR confidence. Individual extracted fields
    can later be adjusted by the decision engine.
    """

    abv = extract_abv(text)
    net_contents = extract_net_contents(text)
    warning = extract_warning(text)
    brand = extract_brand_name(text)
    class_type = extract_class_type(text)
    name_address = extract_name_address(text)
    country = extract_country(text)

    fields: List[ExtractedField] = []

    fields.append(
        ExtractedField(
            field="brand_name",
            value=brand or None,
            confidence=ocr_confidence,
            evidence=brand,
        )
    )

    fields.append(
        ExtractedField(
            field="class_type",
            value=class_type or None,
            confidence=ocr_confidence,
            evidence=class_type,
        )
    )

    fields.append(
        ExtractedField(
            field="abv",
            value=abv or None,
            confidence=ocr_confidence,
            evidence=abv,
        )
    )

    fields.append(
        ExtractedField(
            field="net_contents",
            value=net_contents or None,
            confidence=ocr_confidence,
            evidence=net_contents,
        )
    )

    fields.append(
        ExtractedField(
            field="name_address",
            value=name_address or None,
            confidence=ocr_confidence,
            evidence=name_address,
        )
    )

    fields.append(
        ExtractedField(
            field="country_of_origin",
            value=country or None,
            confidence=ocr_confidence,
            evidence=country,
        )
    )

    fields.append(
        ExtractedField(
            field="government_warning",
            value=warning or None,
            confidence=ocr_confidence,
            evidence=warning,
        )
    )

    return fields


def extraction_summary(
    fields: List[ExtractedField],
) -> Dict[str, str]:
    """
    Convert extracted fields into a simple dictionary.
    """

    return {
        field.field: field.value or ""
        for field in fields
    }

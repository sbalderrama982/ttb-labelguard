import re
import unicodedata
from typing import Optional


def normalize_text(value: Optional[str]) -> str:
    """
    Normalize text for controlled comparison.

    The original value is never modified in the evidence record.
    Normalization is used only for comparison.
    """

    if not value:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        value,
    )

    text = text.encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii"
    )

    text = text.lower()

    # Normalize common OCR punctuation variations.
    text = text.replace("’", "'")
    text = text.replace("`", "'")
    text = text.replace("“", '"')
    text = text.replace("”", '"')

    # Remove punctuation while retaining alphanumeric content.
    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    # Collapse repeated whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize_brand(value: Optional[str]) -> str:
    """
    Brand-specific normalization.

    Apostrophes and punctuation are ignored for comparison,
    while the original text remains available as evidence.
    """

    return normalize_text(value)


def parse_percentage(
    value: Optional[str],
) -> Optional[float]:
    """
    Convert a percentage expression into a numeric value.

    Examples:
        '45%' -> 45.0
        '45 % Alc./Vol.' -> 45.0
        '45.5' -> 45.5
    """

    if not value:
        return None

    match = re.search(
        r"\d+(?:\.\d+)?",
        value,
    )

    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


def parse_volume_ml(
    value: Optional[str],
) -> Optional[float]:
    """
    Convert common metric volume expressions to milliliters.
    """

    if not value:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(ml|l)\b",
        value,
        re.IGNORECASE,
    )

    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2).lower()

    if unit == "l":
        return number * 1000

    return number


def compare_text(
    expected: Optional[str],
    observed: Optional[str],
) -> bool:
    """
    Exact comparison after controlled normalization.
    """

    expected_normalized = normalize_text(
        expected
    )

    observed_normalized = normalize_text(
        observed
    )

    if not expected_normalized or not observed_normalized:
        return False

    return expected_normalized == observed_normalized


def compare_brand(
    expected: Optional[str],
    observed: Optional[str],
) -> bool:
    """
    Compare brand names while tolerating capitalization,
    punctuation, and whitespace differences.
    """

    return compare_text(
        expected,
        observed,
    )


def compare_percentage(
    expected: Optional[float],
    observed: Optional[str],
    tolerance: float = 0.05,
) -> bool:
    """
    Compare numeric percentage values.

    A small tolerance is permitted for OCR representation,
    but not for materially different ABV values.
    """

    if expected is None or not observed:
        return False

    observed_value = parse_percentage(
        observed
    )

    if observed_value is None:
        return False

    return abs(
        expected - observed_value
    ) <= tolerance


def compare_volume(
    expected_ml: Optional[float],
    observed: Optional[str],
) -> bool:
    """
    Compare net contents after converting the observed value
    to milliliters.
    """

    if expected_ml is None or not observed:
        return False

    observed_ml = parse_volume_ml(
        observed
    )

    if observed_ml is None:
        return False

    return abs(
        expected_ml - observed_ml
    ) < 0.1

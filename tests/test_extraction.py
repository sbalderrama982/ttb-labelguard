from labelguard.extraction import (
    extract_abv,
    extract_class_type,
    extract_country,
    extract_net_contents,
    extract_warning,
)


SAMPLE_LABEL = """
STONE'S THROW DISTILLERY
KENTUCKY STRAIGHT BOURBON WHISKEY
45% Alc./Vol. (90 Proof)
750 mL
PRODUCT OF THE UNITED STATES

GOVERNMENT WARNING:
(1) According to the Surgeon General, women should not
drink alcoholic beverages during pregnancy because of
the risk of birth defects.
(2) Consumption of alcoholic beverages impairs your ability
to drive a car or operate machinery, and may cause health
problems.
"""


def test_extract_abv():
    assert extract_abv(
        SAMPLE_LABEL
    ) == "45"


def test_extract_net_contents():
    assert extract_net_contents(
        SAMPLE_LABEL
    ) == "750 mL"


def test_extract_class_type():
    assert extract_class_type(
        SAMPLE_LABEL
    ) == "Kentucky Straight Bourbon Whiskey"


def test_extract_country():
    assert extract_country(
        SAMPLE_LABEL
    ) == "UNITED STATES"


def test_extract_warning():
    warning = extract_warning(
        SAMPLE_LABEL
    )

    assert warning
    assert "GOVERNMENT WARNING:" in warning.upper()
    assert "SURGEON GENERAL" in warning.upper()


def test_missing_abv_returns_empty():
    assert extract_abv(
        "STONE'S THROW BOURBON WHISKEY"
    ) == ""


def test_missing_volume_returns_empty():
    assert extract_net_contents(
        "STONE'S THROW BOURBON WHISKEY"
    ) == ""

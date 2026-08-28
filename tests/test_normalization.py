from labelguard.normalization import (
    compare_brand,
    compare_percentage,
    compare_text,
    compare_volume,
    normalize_text,
    parse_percentage,
    parse_volume_ml,
)


def test_normalize_text_removes_case_and_punctuation():
    assert normalize_text(
        "STONE'S THROW"
    ) == "stone s throw"


def test_brand_comparison_tolerates_case():
    assert compare_brand(
        "STONE'S THROW",
        "Stone's Throw",
    )


def test_brand_comparison_rejects_different_brand():
    assert not compare_brand(
        "STONE'S THROW",
        "STONE'S CREEK",
    )


def test_text_comparison_is_normalized():
    assert compare_text(
        "Kentucky Straight Bourbon Whiskey",
        "KENTUCKY STRAIGHT BOURBON WHISKEY",
    )


def test_percentage_parser():
    assert parse_percentage(
        "45% Alc./Vol."
    ) == 45.0


def test_percentage_comparison():
    assert compare_percentage(
        45.0,
        "45%",
    )


def test_percentage_mismatch():
    assert not compare_percentage(
        45.0,
        "40%",
    )


def test_volume_parser_ml():
    assert parse_volume_ml(
        "750 mL"
    ) == 750.0


def test_volume_parser_liters():
    assert parse_volume_ml(
        "0.75 L"
    ) == 750.0


def test_volume_comparison():
    assert compare_volume(
        750.0,
        "750 mL",
    )


def test_volume_mismatch():
    assert not compare_volume(
        750.0,
        "500 mL",
    )

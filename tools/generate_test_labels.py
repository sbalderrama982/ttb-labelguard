from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path("sample_data/generated")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


LABELS = [
    {
        "filename": "matching_label.png",
        "brand": "STONE'S THROW",
        "class_type": "KENTUCKY STRAIGHT BOURBON WHISKEY",
        "abv": "45% Alc./Vol. (90 Proof)",
        "volume": "750 mL",
        "producer": "STONE'S THROW DISTILLERY",
        "origin": "PRODUCT OF THE UNITED STATES",
        "warning": (
            "GOVERNMENT WARNING: According to the Surgeon General, "
            "women should not drink alcoholic beverages during pregnancy "
            "because of the risk of birth defects."
        ),
    },
    {
        "filename": "abv_mismatch.png",
        "brand": "STONE'S THROW",
        "class_type": "KENTUCKY STRAIGHT BOURBON WHISKEY",
        "abv": "40% Alc./Vol. (80 Proof)",
        "volume": "750 mL",
        "producer": "STONE'S THROW DISTILLERY",
        "origin": "PRODUCT OF THE UNITED STATES",
        "warning": (
            "GOVERNMENT WARNING: According to the Surgeon General, "
            "women should not drink alcoholic beverages during pregnancy."
        ),
    },
    {
        "filename": "brand_mismatch.png",
        "brand": "RIVER BEND RESERVE",
        "class_type": "KENTUCKY STRAIGHT BOURBON WHISKEY",
        "abv": "45% Alc./Vol. (90 Proof)",
        "volume": "750 mL",
        "producer": "STONE'S THROW DISTILLERY",
        "origin": "PRODUCT OF THE UNITED STATES",
        "warning": (
            "GOVERNMENT WARNING: According to the Surgeon General, "
            "women should not drink alcoholic beverages during pregnancy."
        ),
    },
]


def load_font(size: int):
    """
    Try common Linux font locations and fall back to
    Pillow's default font.
    """

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(
                path,
                size,
            )

    return ImageFont.load_default()


def create_label(data):
    """
    Create a synthetic bottle-label-style image.

    These images are intended strictly for prototype testing.
    """

    width = 1400
    height = 1000

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    title_font = load_font(72)
    heading_font = load_font(42)
    body_font = load_font(32)
    warning_font = load_font(23)

    draw.rectangle(
        [40, 40, width - 40, height - 40],
        outline="black",
        width=5,
    )

    y = 90

    draw.text(
        (width // 2, y),
        data["brand"],
        fill="black",
        font=title_font,
        anchor="ma",
    )

    y += 110

    draw.text(
        (width // 2, y),
        data["class_type"],
        fill="black",
        font=heading_font,
        anchor="ma",
    )

    y += 85

    draw.text(
        (width // 2, y),
        data["abv"],
        fill="black",
        font=body_font,
        anchor="ma",
    )

    y += 60

    draw.text(
        (width // 2, y),
        data["volume"],
        fill="black",
        font=body_font,
        anchor="ma",
    )

    y += 75

    draw.text(
        (width // 2, y),
        data["producer"],
        fill="black",
        font=body_font,
        anchor="ma",
    )

    y += 55

    draw.text(
        (width // 2, y),
        data["origin"],
        fill="black",
        font=body_font,
        anchor="ma",
    )

    warning_box_top = height - 330

    draw.rectangle(
        [
            100,
            warning_box_top,
            width - 100,
            height - 100,
        ],
        outline="black",
        width=3,
    )

    draw.text(
        (
            width // 2,
            warning_box_top + 30,
        ),
        data["warning"],
        fill="black",
        font=warning_font,
        anchor="ma",
        align="center",
        spacing=10,
    )

    output_path = (
        OUTPUT_DIR / data["filename"]
    )

    image.save(
        output_path,
        format="PNG",
    )

    print(
        f"Created: {output_path}"
    )


def main():
    for label in LABELS:
        create_label(label)

    print(
        f"\nGenerated {len(LABELS)} synthetic test labels."
    )


if __name__ == "__main__":
    main()

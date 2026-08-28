import io
import re
from typing import Dict, List, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image


def _load_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert uploaded image bytes into an OpenCV image.
    """

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    return cv2.cvtColor(
        np.array(image),
        cv2.COLOR_RGB2BGR,
    )


def _preprocess_variants(image: np.ndarray) -> List[np.ndarray]:
    """
    Produce several lightweight preprocessing variants.

    Multiple variants improve resilience to:
    - uneven lighting
    - low contrast
    - mild glare
    - photographic noise
    - slightly difficult label images
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    # Normalize contrast.
    normalized = cv2.normalize(
        gray,
        None,
        0,
        255,
        cv2.NORM_MINMAX,
    )

    # Adaptive threshold helps with uneven lighting.
    adaptive = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # Otsu threshold provides another OCR-friendly representation.
    _, otsu = cv2.threshold(
        normalized,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    # Light sharpening.
    blurred = cv2.GaussianBlur(
        normalized,
        (0, 0),
        3,
    )

    sharpened = cv2.addWeighted(
        normalized,
        1.5,
        blurred,
        -0.5,
        0,
    )

    return [
        image,
        normalized,
        adaptive,
        otsu,
        sharpened,
    ]


def _run_tesseract(image: np.ndarray) -> Tuple[str, float]:
    """
    Run Tesseract OCR and estimate average confidence.
    """

    rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB,
    )

    data = pytesseract.image_to_data(
        rgb,
        config="--psm 6",
        output_type=pytesseract.Output.DICT,
    )

    words = []
    confidences = []

    for text, confidence in zip(
        data.get("text", []),
        data.get("conf", []),
    ):
        text = text.strip()

        try:
            numeric_confidence = float(confidence)
        except (TypeError, ValueError):
            continue

        if text and numeric_confidence >= 0:
            words.append(text)
            confidences.append(numeric_confidence)

    extracted_text = " ".join(words).strip()

    if confidences:
        average_confidence = (
            sum(confidences) / len(confidences)
        ) / 100.0
    else:
        average_confidence = 0.0

    return extracted_text, average_confidence


def _score_text(text: str) -> int:
    """
    Score OCR output based on the likelihood that it contains
    useful alcohol-label information.
    """

    if not text:
        return 0

    upper = text.upper()

    score = len(text)

    keywords = [
        "GOVERNMENT WARNING",
        "ALC",
        "VOL",
        "PROOF",
        "ML",
        "L",
        "WHISKEY",
        "WHISKY",
        "BOURBON",
        "DISTILLED",
        "WINE",
        "BEER",
        "BREWED",
    ]

    for keyword in keywords:
        if keyword in upper:
            score += 100

    # Presence of percentages is particularly useful.
    if re.search(r"\d+(?:\.\d+)?\s*%", text):
        score += 150

    return score


def extract_text(image_bytes: bytes) -> Dict[str, object]:
    """
    Perform local OCR against several image representations.

    Returns:
        {
            "text": str,
            "confidence": float,
            "variants_used": int
        }
    """

    image = _load_image(image_bytes)

    variants = _preprocess_variants(image)

    candidates = []

    for variant in variants:
        text, confidence = _run_tesseract(variant)

        if text:
            candidates.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "score": _score_text(text),
                }
            )

    if not candidates:
        return {
            "text": "",
            "confidence": 0.0,
            "variants_used": len(variants),
        }

    # Prefer useful text while still considering OCR confidence.
    best = max(
        candidates,
        key=lambda item: (
            item["score"],
            item["confidence"],
        ),
    )

    return {
        "text": best["text"],
        "confidence": float(best["confidence"]),
        "variants_used": len(variants),
    }

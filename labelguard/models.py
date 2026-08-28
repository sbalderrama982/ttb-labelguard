from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ApplicationRecord:
    """
    Information supplied by the label application.

    This prototype intentionally keeps the model small and focused
    on the fields needed for label-to-application verification.
    """

    application_id: str
    beverage_type: str
    brand_name: str
    class_type: str
    abv: Optional[float]
    net_contents_ml: Optional[float]
    name_address: str
    country_of_origin: Optional[str] = None


@dataclass
class ExtractedField:
    """
    A piece of information observed on the physical label.
    """

    field: str
    value: Optional[str]
    confidence: float = 0.0
    evidence: str = ""


@dataclass
class FieldResult:
    """
    Comparison result for one application field.
    """

    field: str
    application: Optional[str]
    observed: Optional[str]
    decision: str
    confidence: float
    reason: str
    evidence: str = ""


@dataclass
class VerificationResult:
    """
    Complete verification result for one uploaded label.
    """

    filename: str
    decision: str
    processing_ms: int
    ocr_confidence: float
    fields: List[FieldResult] = field(default_factory=list)
    review_flags: List[str] = field(default_factory=list)
    extracted_text: str = ""
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result into a JSON-compatible dictionary.
        """

        return {
            "filename": self.filename,
            "decision": self.decision,
            "processing_ms": self.processing_ms,
            "ocr_confidence": self.ocr_confidence,
            "fields": [
                {
                    "field": item.field,
                    "application": item.application,
                    "observed": item.observed,
                    "decision": item.decision,
                    "confidence": item.confidence,
                    "reason": item.reason,
                    "evidence": item.evidence,
                }
                for item in self.fields
            ],
            "review_flags": self.review_flags,
            "extracted_text": self.extracted_text,
            "trace": self.trace,
        }

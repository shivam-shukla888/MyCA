"""
Vision Models and Schemas for myCA AI Document Understanding Engine.
Defines strict structured models for extraction, image quality, and page aggregation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class VisionDocumentType(str, Enum):
    BANK_STATEMENT = "BANK_STATEMENT"
    SALARY_SLIP = "SALARY_SLIP"
    FORM_16 = "FORM_16"
    CREDIT_CARD_STATEMENT = "CREDIT_CARD_STATEMENT"
    LOAN_STATEMENT = "LOAN_STATEMENT"
    MUTUAL_FUND_STATEMENT = "MUTUAL_FUND_STATEMENT"
    DEMAT_STATEMENT = "DEMAT_STATEMENT"
    INSURANCE_DOCUMENT = "INSURANCE_DOCUMENT"
    RECEIPT = "RECEIPT"
    INVOICE = "INVOICE"
    UNKNOWN = "UNKNOWN"

class VisionProcessingStatus(str, Enum):
    AI_EXTRACTED = "AI_EXTRACTED"
    VALIDATED = "VALIDATED"
    READY = "READY"
    USER_CONFIRMED = "USER_CONFIRMED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"

@dataclass
class ImageQualityAssessment:
    is_acceptable: bool = True
    score: float = 1.0
    issues: List[str] = field(default_factory=list)
    message: str = "Image quality is good for processing."
    blur_score: float = 0.0
    glare_score: float = 0.0

@dataclass
class ExtractedTransaction:
    date: str
    description: str
    amount: float
    type: str  # CREDIT or DEBIT
    direction: str = "DEBIT"
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    reference: Optional[str] = None
    confidence: float = 0.95
    source_page: int = 1
    source_region: Optional[str] = None

@dataclass
class VisionExtractionResult:
    document_type: str = VisionDocumentType.UNKNOWN.value
    confidence: float = 0.0
    account: Optional[Dict[str, Any]] = None
    statement_period: Optional[Dict[str, str]] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    salary_record: Optional[Dict[str, Any]] = None
    tax_record: Optional[Dict[str, Any]] = None
    receipt_record: Optional[Dict[str, Any]] = None
    quality_assessment: ImageQualityAssessment = field(default_factory=ImageQualityAssessment)
    pages_data: List[Dict[str, Any]] = field(default_factory=list)
    is_scanned: bool = False
    raw_response: Optional[str] = None
    provider_name: str = "local_vision_engine"
    model_name: str = "vision-deterministic-v1"
    prompt_injection_detected: bool = False
    validation_status: str = VisionProcessingStatus.AI_EXTRACTED.value
    status_message: str = "AI extraction complete."

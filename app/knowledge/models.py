"""
Data models for myCA Financial Knowledge and Grounded Advisory System.
Enforces strict typing, provenance, and separation of concerns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal

class RuleStatus(str, Enum):
    CURRENT = "CURRENT"
    FUTURE = "FUTURE"
    SUPERSEDED = "SUPERSEDED"
    NOT_VERIFIED = "NOT_VERIFIED"

class AdvisoryResponseType(str, Enum):
    OBSERVATION = "OBSERVATION"          # Factual statement grounded in user's data
    CALCULATION = "CALCULATION"          # Result of deterministic mathematical formula
    EDUCATION = "EDUCATION"              # Explanation of statutory rules or financial concepts
    RECOMMENDATION = "RECOMMENDATION"    # Safe financial hygiene guidance (e.g. emergency fund)
    WARNING = "WARNING"                  # Deficit, missing reconciliation, or risk alert
    NEEDS_INFORMATION = "NEEDS_INFO"     # Insufficient personal data to answer accurately
    NEEDS_REVIEW = "NEEDS_REVIEW"        # Data under human verification or discrepancy

@dataclass
class StatutoryRule:
    id: str
    topic: str
    title: str
    content: str
    source: str
    official_source_reference: str
    publication_date: str
    effective_from: str
    effective_to: Optional[str]
    financial_year: str
    assessment_year: str
    provision: str
    jurisdiction: str
    status: RuleStatus
    rule_data: Dict[str, Any]
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    version: int = 1
    last_verified_at: Optional[str] = None

@dataclass
class AdvisoryEvidence:
    source_type: str                   # "USER_DOCUMENT" | "STATUTORY_RULE" | "DETERMINISTIC_CALCULATION"
    source_name: str                   # e.g., "HDFC Bank Statement", "Section 115BAC"
    reference_id: str                  # doc_id or rule_id
    page_number: Optional[int] = None
    status: str = "VERIFIED_FROM_DOCUMENT"
    snippet: str = ""

@dataclass
class GroundedAdvisoryResponse:
    answer: str
    response_type: AdvisoryResponseType
    data_used: Dict[str, Any] = field(default_factory=dict)
    knowledge_used: List[Dict[str, Any]] = field(default_factory=list)
    calculation_used: Optional[str] = None
    sources: List[AdvisoryEvidence] = field(default_factory=list)
    status: str = "GROUNDED_AND_VERIFIED"
    recommendation_disclaimer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "response_type": self.response_type.value,
            "data_used": self.data_used,
            "knowledge_used": self.knowledge_used,
            "calculation_used": self.calculation_used,
            "sources": [
                {
                    "source": s.source_name,
                    "source_name": s.source_name,
                    "source_type": s.source_type,
                    "reference_id": s.reference_id,
                    "page": s.page_number,
                    "status": s.status,
                    "snippet": s.snippet
                }
                for s in self.sources
            ],
            "status": self.status,
            "recommendation_disclaimer": self.recommendation_disclaimer
        }

@dataclass
class TaxSlabBreakdown:
    slab_range: str
    taxable_amount: Decimal
    rate_percent: Decimal
    tax_amount: Decimal

@dataclass
class TaxCalculationResult:
    assessment_year: str
    regime: str
    gross_income: Decimal
    standard_deduction: Decimal
    deductions_80c: Decimal
    deductions_80d: Decimal
    total_deductions: Decimal
    taxable_income: Decimal
    slab_tax: Decimal
    rebate_87a: Decimal
    tax_after_rebate: Decimal
    cess_4_percent: Decimal
    total_tax_payable: Decimal
    effective_rate_percent: Decimal
    slabs_applied: List[TaxSlabBreakdown]
    rule_reference: str
    disclaimer: str

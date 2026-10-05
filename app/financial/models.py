"""
Financial Models and Typed Dataclasses for Normalized Records.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

class TransactionDirection(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    REFUND = "REFUND"
    REVERSAL = "REVERSAL"
    TRANSFER = "TRANSFER"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class DataStatus(str, Enum):
    VERIFIED_FROM_DOCUMENT = "VERIFIED_FROM_DOCUMENT"
    CALCULATED = "CALCULATED"
    USER_CONFIRMED = "USER_CONFIRMED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"
    READY = "READY"

class DuplicateStatus(str, Enum):
    UNIQUE = "UNIQUE"
    DUPLICATE_CONFIRMED = "DUPLICATE_CONFIRMED"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"

@dataclass
class NormalizedTransaction:
    id: str
    user_id: str
    account_id: str
    date_iso: str  # YYYY-MM-DD
    raw_date: str  # e.g. 02/10/2024
    description: str
    cleaned_merchant: str
    amount: Decimal
    direction: TransactionDirection
    balance: Optional[Decimal]
    category: str
    source_document_id: str
    source_page: int
    source_text: str
    status: DataStatus = DataStatus.VERIFIED_FROM_DOCUMENT
    confidence: float = 1.0
    duplicate_status: DuplicateStatus = DuplicateStatus.UNIQUE
    fingerprint: Optional[str] = None
    duplicate_of_id: Optional[str] = None

@dataclass
class StatementReconciliationReport:
    is_valid: bool
    status: DataStatus
    opening_balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    net_cash_flow: Decimal
    calculated_closing: Decimal
    reported_closing: Decimal
    discrepancy: Decimal
    message: str
    explanation: Dict[str, Any] = field(default_factory=dict)

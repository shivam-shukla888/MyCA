"""
myCA Financial Calculation & Extraction Intelligence Package.
"""

from .money import to_decimal, format_inr
from .models import (
    TransactionDirection,
    DataStatus,
    DuplicateStatus,
    NormalizedTransaction,
    StatementReconciliationReport
)
from .normalization import (
    normalize_transaction_dict,
    clean_merchant_name,
    infer_transaction_direction,
    categorize_transaction,
    parse_iso_date
)
from .reconciliation import reconcile_bank_statement
from .calculations import compute_financial_profile_deterministic
from .duplicate import compute_transaction_fingerprint, detect_overlapping_transactions

__all__ = [
    "to_decimal",
    "format_inr",
    "TransactionDirection",
    "DataStatus",
    "DuplicateStatus",
    "NormalizedTransaction",
    "StatementReconciliationReport",
    "normalize_transaction_dict",
    "clean_merchant_name",
    "infer_transaction_direction",
    "categorize_transaction",
    "parse_iso_date",
    "reconcile_bank_statement",
    "compute_financial_profile_deterministic",
    "compute_transaction_fingerprint",
    "detect_overlapping_transactions"
]

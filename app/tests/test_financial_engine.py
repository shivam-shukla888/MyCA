"""
Comprehensive Test Suite for Phase 3 Deterministic Financial Engine.
Tests:
- Decimal precision without floating-point errors
- Transaction normalization and direction classification
- Deterministic reconciliation
- Overlapping statement deduplication
- Refunds, reversals, and internal transfers
- Golden fixtures verification
"""

import unittest
from decimal import Decimal
from app.financial.money import to_decimal, format_inr
from app.financial.models import TransactionDirection, DataStatus, DuplicateStatus
from app.financial.normalization import (
    parse_iso_date,
    clean_merchant_name,
    infer_transaction_direction,
    normalize_transaction_dict
)
from app.financial.reconciliation import reconcile_bank_statement
from app.financial.calculations import compute_financial_profile_deterministic
from app.financial.duplicate import compute_transaction_fingerprint, detect_overlapping_transactions
from app.tests.fixtures.golden_statements import (
    GOLDEN_HDFC_VALID,
    GOLDEN_OVERLAPPING_PAIR,
    GOLDEN_STATEMENT_DISCREPANCY,
    GOLDEN_REFUND_REVERSAL,
    GOLDEN_INTERNAL_TRANSFER
)

class TestFinancialEngine(unittest.TestCase):

    def test_01_safe_decimal_money_precision(self):
        """Monetary values must never suffer binary floating-point drift."""
        # 0.1 + 0.2 in standard binary float is 0.30000000000000004
        d1 = to_decimal(0.1)
        d2 = to_decimal(0.2)
        self.assertEqual(d1 + d2, Decimal('0.30'))

        # Large amounts and comma strings
        large = to_decimal("₹ 10,25,84,950.55")
        self.assertEqual(large, Decimal('102584950.55'))

        # String formatting in Indian Numbering System
        self.assertEqual(format_inr(Decimal('127500.00')), "₹1,27,500.00")
        self.assertEqual(format_inr(Decimal('54300.50')), "₹54,300.50")
        self.assertEqual(format_inr(Decimal('10000000.00')), "₹1,00,00,000.00")

    def test_02_transaction_direction_inference(self):
        """Accurately distinguishes CREDIT, DEBIT, REFUND, REVERSAL, TRANSFER, and NEEDS_REVIEW."""
        self.assertEqual(
            infer_transaction_direction("ACH CR-INFOSYS-SALARY", "CREDIT"),
            TransactionDirection.CREDIT
        )
        self.assertEqual(
            infer_transaction_direction("NEFT DR-HOUSE RENT OCT2024", "DEBIT"),
            TransactionDirection.DEBIT
        )
        self.assertEqual(
            infer_transaction_direction("REFUND-SWIGGY-ORDER-CANCELLED", "CREDIT"),
            TransactionDirection.REFUND
        )
        self.assertEqual(
            infer_transaction_direction("REV-ATM CASH WITHDRAWAL FAILED", "CREDIT"),
            TransactionDirection.REVERSAL
        )
        self.assertEqual(
            infer_transaction_direction("SELF TRANSFER TO DEMAT A/C", "DEBIT"),
            TransactionDirection.TRANSFER
        )
        # Ambiguous record without clear markers
        self.assertEqual(
            infer_transaction_direction("SOMETHING UNKNOWN 92830", "UNKNOWN"),
            TransactionDirection.NEEDS_REVIEW
        )

    def test_03_date_normalization_to_iso(self):
        """Converts Indian statement dates (DD/MM/YYYY) to standard ISO-8601 (YYYY-MM-DD)."""
        self.assertEqual(parse_iso_date("02/10/2024"), "2024-10-02")
        self.assertEqual(parse_iso_date("28-10-2024"), "2024-10-28")
        self.assertEqual(parse_iso_date("15 Oct 2024"), "2024-10-15")

    def test_04_golden_hdfc_reconciliation(self):
        """Golden Fixture 1: Perfect reconciliation on standard HDFC multi-page statement."""
        raw_txs = [
            {"amount": "82000.00", "type": "CREDIT", "direction": "CREDIT"},
            {"amount": "18000.00", "type": "DEBIT", "direction": "DEBIT"},
            {"amount": "9000.00", "type": "DEBIT", "direction": "DEBIT"},
            {"amount": "27300.00", "type": "DEBIT", "direction": "DEBIT"}
        ]
        res = reconcile_bank_statement(
            GOLDEN_HDFC_VALID["opening_balance"],
            GOLDEN_HDFC_VALID["closing_balance"],
            raw_txs
        )
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["discrepancy"], 0.0)
        self.assertEqual(res["total_credits"], 82000.0)
        self.assertEqual(res["total_debits"], 54300.0)
        self.assertEqual(res["net_savings"], 27700.0)

    def test_05_golden_statement_discrepancy_needs_review(self):
        """Golden Fixture 3: Mismatched statement must be flagged NEEDS_REVIEW, never silently fixed."""
        res = reconcile_bank_statement(
            GOLDEN_STATEMENT_DISCREPANCY["opening_balance"],
            GOLDEN_STATEMENT_DISCREPANCY["reported_closing"],
            GOLDEN_STATEMENT_DISCREPANCY["transactions"]
        )
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["discrepancy"], 3200.0)
        self.assertIn("Is statement ka balance match nahi ho raha", res["message"])

    def test_06_overlapping_statements_deduplication(self):
        """Golden Fixture 2: Overlapping statements must classify duplicates and not double count."""
        s1 = GOLDEN_OVERLAPPING_PAIR["statement_1"]
        s2 = GOLDEN_OVERLAPPING_PAIR["statement_2"]

        # Normalize statement 1
        norm_s1 = [normalize_transaction_dict(t, "user_1", "acc_1", "doc_1") for t in s1]
        processed_s1 = detect_overlapping_transactions(norm_s1, {})

        # Build fingerprints map from statement 1
        fingerprints = {t["fingerprint"]: t["id"] for t in processed_s1}

        # Normalize statement 2
        norm_s2 = [normalize_transaction_dict(t, "user_1", "acc_1", "doc_2") for t in s2]
        processed_s2 = detect_overlapping_transactions(norm_s2, fingerprints)

        # In statement 2, Amazon purchase (Oct 15) must be DUPLICATE_CONFIRMED
        amazon_s2 = next(t for t in processed_s2 if "Amazon" in t["description"])
        self.assertEqual(amazon_s2["duplicate_status"], DuplicateStatus.DUPLICATE_CONFIRMED.value)

        rent_s2 = next(t for t in processed_s2 if "Rent" in t["description"])
        self.assertEqual(rent_s2["duplicate_status"], DuplicateStatus.UNIQUE.value)

        # When computing financial profile, duplicates must be ignored
        combined = processed_s1 + processed_s2
        profile = compute_financial_profile_deterministic(combined, filter_duplicates=True)
        self.assertEqual(profile["monthly_expenses"], float(GOLDEN_OVERLAPPING_PAIR["expected_combined_expenses"]))

    def test_07_refunds_and_reversals_accounting(self):
        """Golden Fixture 4: Merchant refunds reduce expenses rather than inflating earned income."""
        txs = [
            {"amount": "1200.00", "type": "DEBIT", "direction": "DEBIT", "category": "Food & Dining"},
            {"amount": "1200.00", "type": "CREDIT", "direction": "REFUND", "category": "Food & Dining"}
        ]
        profile = compute_financial_profile_deterministic(txs)
        self.assertEqual(profile["monthly_income"], 0.0)
        self.assertEqual(profile["monthly_expenses"], 0.0)

    def test_08_internal_transfers_isolation(self):
        """Golden Fixture 5: Internal transfers are isolated and do not count as living expenses."""
        txs = [
            {"amount": "25000.00", "type": "DEBIT", "direction": "TRANSFER", "category": "Transfers"},
            {"amount": "1500.00", "type": "DEBIT", "direction": "DEBIT", "category": "Food & Dining"}
        ]
        profile = compute_financial_profile_deterministic(txs)
        self.assertEqual(profile["monthly_expenses"], 1500.0)
        self.assertEqual(profile["total_transfers"], 25000.0)

if __name__ == "__main__":
    unittest.main()

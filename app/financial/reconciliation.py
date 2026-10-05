"""
Deterministic Bank Statement Reconciliation Engine.
Formula:
Opening Balance + Credits - Debits == Closing Balance
Strictly uses Decimal arithmetic (zero float errors).
Supports Refunds, Reversals, and Zero-Value transactions.
"""

from decimal import Decimal
from typing import List, Dict, Any
from .money import to_decimal, format_inr
from .models import StatementReconciliationReport, DataStatus, TransactionDirection

def reconcile_bank_statement(
    opening_balance_input: Any,
    closing_balance_input: Any,
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Performs deterministic arithmetic reconciliation of statement line items.
    Never silently adjusts numbers.
    """
    opening_balance = to_decimal(opening_balance_input)
    reported_closing = to_decimal(closing_balance_input)

    total_credits = Decimal('0.00')
    total_debits = Decimal('0.00')

    # Sum credits and debits using exact Decimal
    for tx in transactions:
        # Ignore duplicate confirmed records in reconciliation if flag present
        if tx.get("duplicate_status") == "DUPLICATE_CONFIRMED":
            continue

        amt = to_decimal(tx.get("amount", 0))
        direction = tx.get("direction", tx.get("type", "DEBIT"))

        if direction in ("CREDIT", "REFUND"):
            total_credits += amt
        elif direction in ("DEBIT", "TRANSFER"):
            total_debits += amt
        elif direction == "REVERSAL":
            # A reversal can offset a debit or credit; default behavior: credited back
            total_credits += amt

    calculated_closing = opening_balance + total_credits - total_debits
    discrepancy = abs(calculated_closing - reported_closing)

    # Exact zero discrepancy required in Decimal
    is_valid = (discrepancy == Decimal('0.00'))
    status = DataStatus.READY.value if is_valid else DataStatus.NEEDS_REVIEW.value

    msg = (
        "Document ready hai. Numbers verified."
        if is_valid
        else f"Is statement ka balance match nahi ho raha. Discrepancy: {format_inr(discrepancy)}."
    )

    explanation = {
        "formula": "Opening Balance + Total Credits - Total Debits = Closing Balance",
        "inputs": {
            "opening_balance": str(opening_balance),
            "total_credits": str(total_credits),
            "total_debits": str(total_debits),
            "reported_closing": str(reported_closing),
            "calculated_closing": str(calculated_closing),
            "discrepancy": str(discrepancy)
        },
        "verified_at_source": is_valid
    }

    return {
        "is_valid": is_valid,
        "status": status,
        "opening_balance": float(opening_balance),
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "net_savings": float(total_credits - total_debits),
        "calculated_closing": float(calculated_closing),
        "reported_closing": float(reported_closing),
        "discrepancy": float(discrepancy),
        "message": msg,
        "explanation": explanation
    }

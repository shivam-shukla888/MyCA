from typing import Dict, Any

def reconcile_statement_numbers(opening_balance: float, closing_balance: float, transactions: list) -> Dict[str, Any]:
    """
    Deterministically audits bank statement reconciliation:
    opening balance + credits - debits == closing balance
    Never silently corrects discrepancies.
    """
    total_credits = sum(float(tx["amount"]) for tx in transactions if tx["type"] == "CREDIT")
    total_debits = sum(float(tx["amount"]) for tx in transactions if tx["type"] == "DEBIT")
    
    calculated_closing = round(opening_balance + total_credits - total_debits, 2)
    reported_closing = round(closing_balance, 2)
    discrepancy = round(abs(calculated_closing - reported_closing), 2)

    # Tolerance for standard floating point calculations
    is_reconciled = discrepancy <= 0.05

    if is_reconciled:
        return {
            "is_valid": True,
            "status": "READY",
            "opening_balance": opening_balance,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_savings": round(total_credits - total_debits, 2),
            "calculated_closing": calculated_closing,
            "reported_closing": reported_closing,
            "discrepancy": 0.0,
            "message": "Document ready hai. Numbers verified."
        }
    else:
        return {
            "is_valid": False,
            "status": "NEEDS_REVIEW",
            "opening_balance": opening_balance,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_savings": round(total_credits - total_debits, 2),
            "calculated_closing": calculated_closing,
            "reported_closing": reported_closing,
            "discrepancy": discrepancy,
            "message": "Is statement ka balance match nahi ho raha. Please review karein."
        }

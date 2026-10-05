"""
Deterministic Financial Calculations Engine.
Computes:
- Income Total (Credits)
- Expenses Total (Debits)
- Net Cash Flow (Income - Expenses)
- Savings Rate (Savings / Income * 100)
- Category Aggregations & Percentage Breakdowns
- Internal Transfers Isolation (Prevents double counting)
Uses Decimal arithmetic throughout.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from .money import to_decimal, format_inr
from .models import TransactionDirection, DataStatus

def compute_financial_profile_deterministic(
    transactions: List[Dict[str, Any]],
    filter_duplicates: bool = True
) -> Dict[str, Any]:
    """
    Computes financial summaries, savings rates, and expense allocations
    strictly using Decimal arithmetic.
    Filters out confirmed duplicates and treats transfers safely.
    """
    total_income = Decimal('0.00')
    total_expenses = Decimal('0.00')
    total_transfers = Decimal('0.00')
    category_map: Dict[str, Decimal] = {}

    valid_txs = []
    for tx in transactions:
        if filter_duplicates and tx.get("duplicate_status") == "DUPLICATE_CONFIRMED":
            continue
        valid_txs.append(tx)

    for tx in valid_txs:
        amt = to_decimal(tx.get("amount", 0.0))
        tx_type = tx.get("type", "DEBIT")
        direction = tx.get("direction")
        if tx_type == "CREDIT" and direction == "DEBIT":
            direction = "CREDIT"
        elif not direction:
            direction = tx_type

        if direction == "CREDIT":
            total_income += amt
        elif direction == "REFUND":
            # Refund offsets expenses rather than inflating primary earned income
            total_expenses -= amt
        elif direction == "TRANSFER":
            # Internal transfers are tracked separately to prevent false expense inflation
            total_transfers += amt
        elif direction in ("DEBIT", "REVERSAL"):
            total_expenses += amt
            cat = tx.get("category", "Miscellaneous")
            category_map[cat] = category_map.get(cat, Decimal('0.00')) + amt

    # Floor expenses at 0 in case refunds exceed expenses in an isolated test period
    if total_expenses < Decimal('0.00'):
        total_expenses = Decimal('0.00')

    net_savings = total_income - total_expenses

    if total_income > Decimal('0.00'):
        savings_rate = ((net_savings / total_income) * Decimal('100.0')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    else:
        savings_rate = Decimal('0.0')

    # Category breakdowns sorted descending
    sorted_cats = sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    categories_breakdown = []
    for cat_name, cat_amt in sorted_cats:
        if total_expenses > Decimal('0.00'):
            pct = ((cat_amt / total_expenses) * Decimal('100.0')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        else:
            pct = Decimal('0.0')
        categories_breakdown.append({
            "category": cat_name,
            "amount": float(cat_amt),
            "percentage": float(pct)
        })

    # High-level expense buckets
    food_total = category_map.get("Food & Dining", Decimal('0.00'))
    shopping_total = category_map.get("Shopping", Decimal('0.00'))
    rent_total = category_map.get("Rent", Decimal('0.00'))
    loan_total = category_map.get("Loans & EMI", Decimal('0.00'))

    # Actionable guidance
    if net_savings >= Decimal('10000.00'):
        buffer_rec = Decimal('10000.00')
    elif net_savings > Decimal('0.00'):
        buffer_rec = max(Decimal('1000.00'), (net_savings * Decimal('0.4')).quantize(Decimal('1.00'), rounding=ROUND_HALF_UP))
    else:
        buffer_rec = Decimal('0.00')

    next_step = {
        "title": "Agla step",
        "description": f"₹{int(net_savings):,} bach rahe hain. Aap ₹{int(buffer_rec):,} emergency fund mein rakh sakte hain.",
        "action_label": "Samjhao",
        "action_payload": {
            "type": "EMERGENCY_FUND_ALLOCATION",
            "suggested_amount": float(buffer_rec),
            "liquid_surplus": float(net_savings)
        }
    }

    # Traceable calculation provenance
    calculation_explanation = {
        "income_formula": "Sum of verified credit transactions",
        "expense_formula": "Sum of debits - verified merchant refunds",
        "net_cash_flow_formula": "Total Income - Total Expenses",
        "savings_rate_formula": "(Net Savings / Total Income) * 100",
        "values": {
            "income": str(total_income),
            "expenses": str(total_expenses),
            "transfers": str(total_transfers),
            "savings": str(net_savings),
            "savings_rate": str(savings_rate)
        },
        "status": DataStatus.CALCULATED.value
    }

    return {
        "monthly_income": float(total_income),
        "monthly_expenses": float(total_expenses),
        "monthly_savings": float(net_savings),
        "savings_rate": float(savings_rate),
        "total_transfers": float(total_transfers),
        "categories": categories_breakdown,
        "top_expenses": {
            "rent": float(rent_total),
            "food": float(food_total),
            "shopping": float(shopping_total),
            "loans": float(loan_total)
        },
        "next_step": next_step,
        "calculation_explanation": calculation_explanation
    }

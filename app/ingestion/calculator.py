from typing import List, Dict, Any

def compute_financial_profile(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic calculation of financial metrics, category aggregations,
    and user guidance. LLM is NEVER used for mathematical truth.
    """
    total_income = 0.0
    total_expenses = 0.0
    category_map = {}

    for tx in transactions:
        amt = float(tx["amount"])
        if tx["type"] == "CREDIT":
            total_income += amt
        else:
            total_expenses += amt
            cat = tx.get("category", "Miscellaneous")
            category_map[cat] = category_map.get(cat, 0.0) + amt

    total_income = round(total_income, 2)
    total_expenses = round(total_expenses, 2)
    savings = round(total_income - total_expenses, 2)
    savings_rate = round((savings / total_income * 100), 1) if total_income > 0 else 0.0

    # Sort categories descending
    sorted_cats = sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    categories_breakdown = [
        {"category": k, "amount": round(v, 2), "percentage": round((v / total_expenses * 100), 1) if total_expenses > 0 else 0.0}
        for k, v in sorted_cats
    ]

    # Specific highlighted categories for Home display
    food_total = round(category_map.get("Food & Dining", 0.0), 2)
    shopping_total = round(category_map.get("Shopping", 0.0), 2)
    rent_total = round(category_map.get("Rent", 0.0), 2)
    loan_total = round(category_map.get("Loans & EMI", 0.0), 2)

    # Next actionable step recommendation (pure rule-based deterministic advice)
    recommended_emergency_buffer = 10000.0 if savings >= 10000.0 else max(1000.0, round(savings * 0.4, 2))
    
    next_step = {
        "title": "Agla step",
        "description": f"₹{savings:,.0f} bach rahe hain. Aap ₹{recommended_emergency_buffer:,.0f} emergency fund mein rakh sakte hain.",
        "action_label": "Samjhao",
        "action_payload": {
            "type": "EMERGENCY_FUND_ALLOCATION",
            "suggested_amount": recommended_emergency_buffer,
            "liquid_surplus": savings
        }
    }

    return {
        "monthly_income": total_income,
        "monthly_expenses": total_expenses,
        "monthly_savings": savings,
        "savings_rate": savings_rate,
        "categories": categories_breakdown,
        "top_expenses": {
            "rent": rent_total,
            "food": food_total,
            "shopping": shopping_total,
            "loans": loan_total
        },
        "next_step": next_step
    }

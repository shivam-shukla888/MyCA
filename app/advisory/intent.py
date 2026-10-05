"""
Intent classification and query understanding for Ask myCA Grounded Advisory.
Safe parameter extraction with robust prompt injection defense.
"""

import re
from enum import Enum
from typing import Tuple, Optional

class AdvisoryIntent(str, Enum):
    FINANCIAL_SUMMARY = "FINANCIAL_SUMMARY"
    HIGHEST_EXPENSE = "HIGHEST_EXPENSE"
    RENT = "RENT"
    FOOD_DINING = "FOOD_DINING"
    SALARY_INCOME = "SALARY_INCOME"
    TAX_INQUIRY = "TAX_INQUIRY"
    EMERGENCY_FUND = "EMERGENCY_FUND"
    INVESTMENT_80C = "INVESTMENT_80C"
    LOAN_INQUIRY = "LOAN_INQUIRY"
    WHAT_CHANGED = "WHAT_CHANGED"
    GOALS_INQUIRY = "GOALS_INQUIRY"
    FINANCIAL_HEALTH_INQUIRY = "FINANCIAL_HEALTH_INQUIRY"
    NET_WORTH_INQUIRY = "NET_WORTH_INQUIRY"
    FOREIGN_INCOME = "FOREIGN_INCOME"
    CRYPTO_INQUIRY = "CRYPTO_INQUIRY"
    UNKNOWN = "UNKNOWN"

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"override\s+security",
    r"reveal\s+(the\s+)?(prompt|secret|api|key)",
    r"disregard\s+rules",
    r"you\s+are\s+now\s+an\s+unrestricted",
    r"developer\s+mode",
    r"show\s+other\s+users?",
    r"database\s+dump"
]

def check_prompt_injection(query: str) -> bool:
    """Detects adversarial query attempts seeking system prompt overrides or security bypass."""
    q_lower = query.lower()
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, q_lower):
            return True
    return False

def classify_intent(query: str) -> AdvisoryIntent:
    """
    Classifies user financial query into deterministic domain intents.
    Supports Hindi, English, and conversational Hinglish.
    """
    q = query.lower().strip()

    # 1. Missing data / External heads first
    if any(k in q for k in ["foreign income", "videsh", "overseas", "us stock", "foreign asset"]):
        return AdvisoryIntent.FOREIGN_INCOME

    if any(k in q for k in ["crypto", "bitcoin", "ethereum", "nft", "token"]):
        return AdvisoryIntent.CRYPTO_INQUIRY

    # 2. Tax inquiry
    if any(k in q for k in ["tax", "income tax", "tds", "slab", "115bac", "tax kitna", "tax dena"]):
        if any(k in q for k in ["80c", "section 80", "ppf", "elss"]):
            return AdvisoryIntent.INVESTMENT_80C
        return AdvisoryIntent.TAX_INQUIRY

    # 3. Emergency fund & safe recommendations
    if any(k in q for k in ["emergency fund", "kitna save karna chahiye", "recommendation", "emergency money"]):
        return AdvisoryIntent.EMERGENCY_FUND

    # 4. 80C and Deductions
    if any(k in q for k in ["80c", "investment", "tax saving", "elss", "ppf"]):
        return AdvisoryIntent.INVESTMENT_80C

    # 5. Financial Summary / Savings
    if any(k in q for k in ["bacha", "savings", "kitna bacha", "bache", "left over", "net savings", "overview", "summary"]):
        return AdvisoryIntent.FINANCIAL_SUMMARY

    # 6. Highest expense
    if any(k in q for k in ["sabse zyada", "highest", "max expense", "kahan ja raha", "where money goes", "biggest expense"]):
        return AdvisoryIntent.HIGHEST_EXPENSE

    # 7. Rent
    if any(k in q for k in ["rent", "kiraya", "makan", "flat"]):
        return AdvisoryIntent.RENT

    # 8. Food & Dining
    if any(k in q for k in ["food", "swiggy", "zomato", "khana", "dining", "grocer"]):
        return AdvisoryIntent.FOOD_DINING

    # 9. Salary / Income
    if any(k in q for k in ["salary", "income", "aaya", "kamayi", "tankhwah", "pay"]):
        return AdvisoryIntent.SALARY_INCOME

    # 10. What Changed / Spending Increase
    if any(k in q for k in ["what changed", "kya badla", "kyu badh gaya", "kyun badha", "spending increase", "kharcha badh", "difference"]):
        return AdvisoryIntent.WHAT_CHANGED

    # 11. Goals inquiry
    if any(k in q for k in ["goal", "goals", "lakshya", "target", "emergency fund goal"]):
        return AdvisoryIntent.GOALS_INQUIRY

    # 12. Financial Health
    if any(k in q for k in ["financial health", "health score", "health status", "financial situation"]):
        return AdvisoryIntent.FINANCIAL_HEALTH_INQUIRY

    # 13. Net Worth
    if any(k in q for k in ["net worth", "total assets", "assets minus liabilities"]):
        return AdvisoryIntent.NET_WORTH_INQUIRY

    # 14. Loans
    if any(k in q for k in ["loan", "emi", "karza", "interest rate"]):
        return AdvisoryIntent.LOAN_INQUIRY

    return AdvisoryIntent.UNKNOWN

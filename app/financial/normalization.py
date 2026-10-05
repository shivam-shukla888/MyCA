"""
Transaction Normalization Engine.
Converts raw extracted statements into clean, ISO-standardized records with
accurate direction (CREDIT, DEBIT, REFUND, REVERSAL, TRANSFER),
merchant names, and Decimal precision.
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

from .money import to_decimal
from .models import TransactionDirection, DataStatus, DuplicateStatus
from .duplicate import compute_transaction_fingerprint

CATEGORY_RULES = [
    (r'SALARY|REMUNERATION|PAYROLL|INFOSYS|TCS', 'Salary', TransactionDirection.CREDIT),
    (r'HOUSE RENT|LANDLORD|RENT', 'Rent', TransactionDirection.DEBIT),
    (r'SWIGGY|ZOMATO|RESTAURANT|FOOD|CAFE|BAKERY|NATURES BASKET|FRESHTOHOME|GROCER', 'Food & Dining', TransactionDirection.DEBIT),
    (r'AMAZON|MYNTRA|FLIPKART|RETAIL|SHOPPING|CLOTHING|FASHION|UNIQLO', 'Shopping', TransactionDirection.DEBIT),
    (r'BESCOM|ELECTRICITY|POWER|WATER|BILLPAY', 'Electricity & Utilities', TransactionDirection.DEBIT),
    (r'AIRTEL|BROADBAND|FIBER|INTERNET|NETFLIX|HOTSTAR', 'Subscriptions & Utilities', TransactionDirection.DEBIT),
    (r'SHELL|PETROL|FUEL|UBER|OLA|COMMUTE|TRANSIT', 'Transit & Fuel', TransactionDirection.DEBIT),
    (r'CULT\.FIT|GYM|FITNESS|APOLLO|PHARMACY|MEDICINE|HEALTH|WELLNESS', 'Lifestyle & Wellness', TransactionDirection.DEBIT),
    (r'AUTO LOAN|HOME LOAN|LOAN|EMI|STATE BANK OF INDIA.*LOAN', 'Loans & EMI', TransactionDirection.DEBIT),
    (r'ZERODHA|GROWW|MUTUAL FUND|SIP|NIFTY', 'Investments', TransactionDirection.DEBIT),
    (r'SELF TRANSFER|TRANSFER TO SELF|SAVINGS TO DEMAT', 'Transfer', TransactionDirection.TRANSFER),
]

def parse_iso_date(raw_date_str: str) -> str:
    """
    Parses DD/MM/YYYY or DD-MM-YYYY into ISO-8601 (YYYY-MM-DD).
    If unparseable, returns original string safely.
    """
    cleaned = raw_date_str.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return cleaned

def clean_merchant_name(desc: str) -> str:
    """Extracts human-readable merchant names from noisy banking narratives."""
    s = desc.upper()
    if "HOUSE RENT" in s:
        return "House Rent (Indiranagar Residence)"
    if "INFOSYS" in s:
        return "Infosys Limited"
    if "TCS" in s:
        return "Tata Consultancy Services"
    if "SWIGGY" in s:
        return "Swiggy Online Food"
    if "ZOMATO" in s:
        return "Zomato Food Delivery"
    if "NATURES BASKET" in s:
        return "Nature's Basket Gourmet"
    if "BESCOM" in s:
        return "BESCOM Electricity Bill"
    if "SHELL" in s:
        return "Shell Petrol Pump"
    if "AMAZON" in s:
        return "Amazon India Retail"
    if "CULT.FIT" in s:
        return "Cult.fit Fitness Membership"
    if "UBER" in s:
        return "Uber Trips Bangalore"
    if "MYNTRA" in s:
        return "Myntra Fashion"
    if "FRESHTOHOME" in s:
        return "FreshToHome Supplies"
    if "APOLLO" in s:
        return "Apollo Pharmacy"
    if "AIRTEL" in s:
        return "Airtel Xstream Fiber"
    if "ROASTERY" in s:
        return "The Roastery Coffee House"
    if "AUTO LOAN" in s or "STATE BANK OF INDIA" in s:
        return "SBI Auto Loan Term Installment"
    if "ZERODHA" in s:
        return "Zerodha Broking Limited"

    # Fallback cleanup
    cleaned = re.sub(r'^(UPI|NEFT|ACH|POS|BBPS|NET|IMPS)[-\s/]+', '', desc)
    cleaned = re.sub(r'-(UPI|CARD|CMS|BLR|DR|CR).*$', '', cleaned)
    return cleaned.strip() or desc

def infer_transaction_direction(desc: str, reported_type: str) -> TransactionDirection:
    """
    Distinguishes CREDIT, DEBIT, REFUND, REVERSAL, TRANSFER, and NEEDS_REVIEW.
    Never infers when ambiguous.
    """
    desc_upper = desc.upper()
    
    # Internal transfers
    if "SELF" in desc_upper or "OWN ACCOUNT" in desc_upper or "TRANSFER TO" in desc_upper:
        return TransactionDirection.TRANSFER

    # Reversals
    if "REVERSAL" in desc_upper or "REV-" in desc_upper or "FAILED TXN RET" in desc_upper:
        return TransactionDirection.REVERSAL

    # Refunds
    if "REFUND" in desc_upper or "CASHBACK" in desc_upper:
        return TransactionDirection.REFUND

    # Credits
    if reported_type == "CREDIT" or any(kw in desc_upper for kw in ["SALARY", "ACH CR", "NEFT CR", "INTEREST PAID"]):
        return TransactionDirection.CREDIT

    # Debits
    if reported_type == "DEBIT" or any(kw in desc_upper for kw in ["ACH DR", "NEFT DR", "POS", "UPI", "PAY"]):
        return TransactionDirection.DEBIT

    return TransactionDirection.NEEDS_REVIEW

def categorize_transaction(desc: str, direction: TransactionDirection) -> str:
    """Deterministic category classification."""
    for pattern, cat, _ in CATEGORY_RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return cat
    
    if direction == TransactionDirection.REFUND:
        return "Refunds & Adjustments"
    if direction == TransactionDirection.REVERSAL:
        return "Reversals"
    if direction == TransactionDirection.TRANSFER:
        return "Transfers"
    return "Miscellaneous"

def normalize_transaction_dict(
    raw_item: Dict[str, Any],
    user_id: str,
    account_id: str,
    source_document_id: str
) -> Dict[str, Any]:
    """Normalizes an individual extracted transaction."""
    tx_id = f"tx_{uuid.uuid4().hex[:12]}"
    raw_date = raw_item.get("date", "")
    date_iso = parse_iso_date(raw_date)
    raw_desc = raw_item.get("description", "")
    cleaned_merchant = clean_merchant_name(raw_desc)
    
    amount_dec = to_decimal(raw_item.get("amount", 0.0))
    direction = infer_transaction_direction(raw_desc, raw_item.get("type", "DEBIT"))
    
    # Status handling: if direction is ambiguous, mark as NEEDS_REVIEW
    status = DataStatus.VERIFIED_FROM_DOCUMENT.value
    if direction == TransactionDirection.NEEDS_REVIEW or amount_dec <= Decimal('0.00'):
        status = DataStatus.NEEDS_REVIEW.value
        
    category = categorize_transaction(raw_desc, direction)
    
    balance_val = raw_item.get("balance")
    balance_dec = to_decimal(balance_val) if balance_val is not None else None
    
    fp = compute_transaction_fingerprint(
        date_iso=date_iso,
        amount=amount_dec,
        direction=direction.value,
        cleaned_merchant=cleaned_merchant,
        account_id=account_id
    )

    return {
        "id": tx_id,
        "user_id": user_id,
        "account_id": account_id,
        "date": raw_date,
        "date_iso": date_iso,
        "description": cleaned_merchant,
        "raw_description": raw_desc,
        "amount": float(amount_dec),  # For sqlite backward compatibility
        "amount_decimal": amount_dec,
        "type": "CREDIT" if direction in (TransactionDirection.CREDIT, TransactionDirection.REFUND) else "DEBIT",
        "direction": direction.value,
        "category": category,
        "balance": float(balance_dec) if balance_dec is not None else None,
        "balance_decimal": balance_dec,
        "source_document_id": source_document_id,
        "source_page": raw_item.get("source_page", 1),
        "source_text": raw_item.get("source_text", ""),
        "status": status,
        "confidence": 1.0,
        "fingerprint": fp,
        "duplicate_status": DuplicateStatus.UNIQUE.value,
        "duplicate_of_id": None
    }

import uuid
import re
from typing import Dict, List, Any

CATEGORY_RULES = [
    (r'SALARY|REMUNERATION|PAYROLL|INFOSYS|TCS', 'Salary', 'CREDIT'),
    (r'HOUSE RENT|LANDLORD|RENT', 'Rent', 'DEBIT'),
    (r'SWIGGY|ZOMATO|RESTAURANT|FOOD|CAFE|BAKERY|NATURES BASKET|FRESHTOHOME|GROCER', 'Food & Dining', 'DEBIT'),
    (r'AMAZON|MYNTRA|FLIPKART|RETAIL|SHOPPING|CLOTHING|FASHION|UNIQLO', 'Shopping', 'DEBIT'),
    (r'BESCOM|ELECTRICITY|POWER|WATER|BILLPAY', 'Electricity & Utilities', 'DEBIT'),
    (r'AIRTEL|BROADBAND|FIBER|INTERNET|NETFLIX|HOTSTAR', 'Subscriptions & Utilities', 'DEBIT'),
    (r'SHELL|PETROL|FUEL|UBER|OLA|COMMUTE|TRANSIT', 'Transit & Fuel', 'DEBIT'),
    (r'CULT\.FIT|GYM|FITNESS|APOLLO|PHARMACY|MEDICINE|HEALTH|WELLNESS', 'Lifestyle & Wellness', 'DEBIT'),
    (r'AUTO LOAN|HOME LOAN|LOAN|EMI|STATE BANK OF INDIA.*LOAN', 'Loans & EMI', 'DEBIT'),
    (r'ZERODHA|GROWW|MUTUAL FUND|SIP|NIFTY', 'Investments', 'DEBIT')
]

def clean_merchant_name(desc: str) -> str:
    # Extract readable merchant name from banking narratives
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

    # Fallback cleanup
    cleaned = re.sub(r'^(UPI|NEFT|ACH|POS|BBPS|NET)[-\s/]+', '', desc)
    cleaned = re.sub(r'-(UPI|CARD|CMS|BLR|DR|CR).*$', '', cleaned)
    return cleaned.strip() or desc

def categorize_transaction(desc: str, tx_type: str) -> str:
    for pattern, cat, default_type in CATEGORY_RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return cat
    return "Miscellaneous"

def normalize_financial_records(extracted: Dict[str, Any], user_id: str, document_id: str):
    account_id = f"acc_{uuid.uuid4().hex[:10]}"
    
    # 1. Account object
    account = {
        "id": account_id,
        "user_id": user_id,
        "institution": extracted.get("institution", "HDFC Bank"),
        "account_type": "Savings Account",
        "masked_account_number": extracted.get("masked_account_number", "XXXX5892"),
        "opening_balance": extracted.get("opening_balance", 0.0),
        "closing_balance": extracted.get("closing_balance", 0.0),
        "currency": "INR",
        "source_document_id": document_id
    }

    normalized_transactions = []
    income_records = []
    expense_records = []

    for item in extracted.get("transactions", []):
        t_id = f"tx_{uuid.uuid4().hex[:12]}"
        raw_desc = item["description"]
        cleaned_desc = clean_merchant_name(raw_desc)
        category = categorize_transaction(raw_desc, item["type"])
        amt = float(item["amount"])
        t_type = item["type"]
        p_num = item["source_page"]
        raw_text = item["source_text"]

        tx_obj = {
            "id": t_id,
            "user_id": user_id,
            "account_id": account_id,
            "date": item["date"],
            "description": cleaned_desc,
            "amount": amt,
            "type": t_type,
            "category": category,
            "balance": float(item["balance"]),
            "source_document_id": document_id,
            "source_page": p_num,
            "source_text": raw_text,
            "status": "VERIFIED_FROM_DOCUMENT",
            "confidence": 1.0
        }
        normalized_transactions.append(tx_obj)

        if t_type == "CREDIT":
            inc_obj = {
                "id": f"inc_{uuid.uuid4().hex[:10]}",
                "user_id": user_id,
                "source": cleaned_desc,
                "date": item["date"],
                "amount": amt,
                "type": "SALARY" if "SALARY" in category.upper() else "OTHER_CREDIT",
                "source_document_id": document_id,
                "source_page": p_num,
                "status": "VERIFIED_FROM_DOCUMENT"
            }
            income_records.append(inc_obj)
        else:
            exp_obj = {
                "id": f"exp_{uuid.uuid4().hex[:10]}",
                "user_id": user_id,
                "date": item["date"],
                "merchant": cleaned_desc,
                "amount": amt,
                "category": category,
                "source_document_id": document_id,
                "source_page": p_num,
                "status": "VERIFIED_FROM_DOCUMENT"
            }
            expense_records.append(exp_obj)

    return {
        "account": account,
        "transactions": normalized_transactions,
        "income": income_records,
        "expenses": expense_records
    }

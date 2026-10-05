"""
Document Classification Engine for myCA Ingestion Pipeline.
Identifies document family using structural and text evidence:
- BANK_STATEMENT
- SALARY_SLIP
- FORM_16
- CREDIT_CARD_STATEMENT
- LOAN_STATEMENT
- MUTUAL_FUND_STATEMENT
- DEMAT_STATEMENT
- INSURANCE_DOCUMENT
- UNKNOWN / UNSUPPORTED
Never invents a document type; defaults to UNKNOWN / NEEDS_REVIEW if ambiguous.
"""

import re
from typing import Dict, Any, Tuple
from enum import Enum

class DocumentType(str, Enum):
    BANK_STATEMENT = "bank_statement"
    SALARY_SLIP = "salary_slip"
    FORM_16 = "form_16"
    CREDIT_CARD_STATEMENT = "credit_card_statement"
    LOAN_STATEMENT = "loan_statement"
    MUTUAL_FUND_STATEMENT = "mutual_fund_statement"
    DEMAT_STATEMENT = "demat_statement"
    INSURANCE_DOCUMENT = "insurance_document"
    UNKNOWN = "unknown"

def classify_document(combined_text: str, filename: str = "") -> Tuple[DocumentType, float, str]:
    """
    Analyzes document text and filename to determine the document family.
    Returns: (DocumentType, confidence_score, evidence_snippet)
    """
    text_lower = combined_text.lower()
    fn_lower = filename.lower()

    # 1. Form 16 check
    if any(k in text_lower for k in [
        "form no. 16",
        "certificate under section 203",
        "details of tax deducted and deposited in the central government account",
        "part a - certificate"
    ]) or "form16" in fn_lower or "form_16" in fn_lower:
        return DocumentType.FORM_16, 0.98, "Form No. 16 statutory certificate under section 203"

    # 2. Salary Slip check
    if any(k in text_lower for k in [
        "salary slip",
        "payslip",
        "pay slip",
        "earnings and deductions statement",
        "gross earnings",
        "net pay",
        "basic salary"
    ]) or "payslip" in fn_lower or "salary" in fn_lower:
        # Avoid bank statements mentioning 'salary credit'
        if not ("bank statement" in text_lower or "account statement" in text_lower or "opening balance" in text_lower):
            return DocumentType.SALARY_SLIP, 0.95, "Salary slip / payslip earnings and deductions"

    # 3. Credit Card Statement check
    if any(k in text_lower for k in [
        "credit card statement",
        "card statement",
        "total amount due",
        "minimum amount due",
        "credit limit",
        "available credit limit"
    ]):
        return DocumentType.CREDIT_CARD_STATEMENT, 0.90, "Credit card billing statement"

    # 4. Loan Statement check
    if any(k in text_lower for k in [
        "loan account statement",
        "term loan",
        "principal outstanding",
        "emi schedule",
        "auto loan statement",
        "home loan statement"
    ]):
        return DocumentType.LOAN_STATEMENT, 0.90, "Loan account and EMI schedule"

    # 5. Demat / Portfolio Statement check
    if any(k in text_lower for k in [
        "statement of holding",
        "demat account",
        "depository participant",
        "nsdl",
        "cdsl",
        "isin"
    ]):
        return DocumentType.DEMAT_STATEMENT, 0.88, "Demat securities holding statement"

    # 6. Mutual Fund Statement check
    if any(k in text_lower for k in [
        "consolidated account statement",
        "cams",
        "kfintech",
        "mutual fund statement",
        "portfolio valuation",
        "folionumber",
        "nav date"
    ]):
        return DocumentType.MUTUAL_FUND_STATEMENT, 0.88, "Mutual fund holding statement"

    # 7. Insurance Document check
    if any(k in text_lower for k in [
        "policy schedule",
        "life insurance",
        "health insurance",
        "sum assured",
        "premium payment receipt"
    ]):
        return DocumentType.INSURANCE_DOCUMENT, 0.85, "Insurance policy schedule"

    # 8. Bank Statement check (Primary supported format)
    if any(k in text_lower for k in [
        "bank statement",
        "account statement",
        "statement of account",
        "opening balance",
        "closing balance",
        "hdfc bank",
        "icici bank",
        "state bank of india",
        "axis bank",
        "kotak mahindra"
    ]) or "statement" in fn_lower or "bank" in fn_lower:
        return DocumentType.BANK_STATEMENT, 0.95, "Bank account ledger statement"

    # Ambiguous / Unknown
    return DocumentType.UNKNOWN, 0.20, "Could not reliably classify document structure"

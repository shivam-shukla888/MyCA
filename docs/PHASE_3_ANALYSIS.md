# myCA — Phase 3 Comprehensive Analysis: Financial Calculation Engine & Extraction Intelligence

**Date**: October 6, 2026  
**Status**: COMPLETED & READY FOR EXECUTION  
**Author**: Implementation Agent (Antigravity)  
**Reference Mandate**: Phase 3 Objective & Controls  

---

## 1. Executive Summary

Following the approval of Phase 2 (Security Foundation) with 21/21 passing automated tests, Phase 3 focuses on hardening the **deterministic financial calculation and document-extraction intelligence layer**.

The core operational principle remains:
```text
USER DOCUMENT
      ↓
EXTRACTION (PyMuPDF layout + text blocks + table boundary extraction)
      ↓
NORMALIZATION (Decimal precision, transaction direction, merchant cleanup)
      ↓
VALIDATION (Reconciliation: Opening + Credits - Debits == Closing)
      ↓
DETERMINISTIC CALCULATION (Income, Expenses, Net Cash Flow, Savings Rate)
      ↓
FINANCIAL RECORD (Persisted in SQLite with tenant isolation)
      ↓
SOURCE / PROVENANCE (Traceable page number, source snippet, status)
      ↓
myCA UI (Sovereign Ledger warm ivory visual language)
      ↓
AI EXPLANATION (Explains already-computed numbers, NEVER computes arithmetic)
```

---

## 2. Existing Extraction Architecture Review

### 2.1 What PyMuPDF Currently Extracts
- In `app/ingestion/extractor.py`, `fitz.open(stream=file_bytes, filetype="pdf")` iterates over document pages.
- Currently extracts:
  1. `page_text = page.get_text("text")` (raw text).
  2. Prompt injection patterns via `detect_prompt_injection(page_text)`.
  3. Image presence check via `page.get_images()`.
  4. Average characters per page heuristic (`total_chars < 40 * len(doc)`) to classify scanned vs text documents.
  5. Account holder name and account number patterns via regular expressions.
  6. Opening and closing balances via `Opening\s*Balance[^\d]*([0-9,]+\.[0-9]{2})`.
  7. Line-by-line regex parsing (`tx_regex`), with a fallback to `page.find_tables()` if line splitting produces fewer than 5 transactions.

### 2.2 Table and Transaction Detection
- Transactions are extracted by detecting lines starting with date format `DD/MM/YYYY` or `DD-MM-YYYY`, followed by description text and monetary amounts at the end of the line.
- The table extractor (`page.find_tables()`) extracts structured grid rows:
  - Column 0: Date
  - Column 1: Narrative / Description
  - Column 2: Chq / Ref No.
  - Column 3: Debit
  - Column 4: Credit
  - Column 5: Balance

### 2.3 Date Parsing
- Extracted using `(\d{2}[/-]\d{2}[/-]\d{4})` (e.g. `02/10/2024` or `02-10-2024`).
- Currently kept as raw formatted string without ISO-8601 (`YYYY-MM-DD`) standardization, which creates risks for chronological sorting, date range filtering, and statement overlap detection.

### 2.4 Amount Parsing & Binary Float Hazards
- Currently parsed using `float(val_str.replace(',', ''))`.
- **CRITICAL WEAKNESS**: Floats introduce IEEE-754 precision issues (e.g. `0.1 + 0.2 != 0.3`). In financial systems, accumulating floats leads to balance discrepancies, rounding drift, and false-positive reconciliation errors.

### 2.5 Credits vs Debits Classification
- In `extractor.py`, if multiple amounts are found, the text is scanned for credit keywords:
  `["CR-", "CREDIT", "SALARY", "REFUND", "INTEREST PAID"]`.
- In `normalizer.py`, regex rules match descriptions to categories and default directions.
- In `find_tables()` fallback, row columns for `Debit` and `Credit` are read directly.

### 2.6 Balance Reconciliation
- In `app/ingestion/validator_layer.py`:
  `calculated_closing = round(opening_balance + total_credits - total_debits, 2)`
  `discrepancy = round(abs(calculated_closing - reported_closing), 2)`
  Tolerance is set to `0.05` for float errors.

### 2.7 Provenance Storage
- Each transaction stores:
  - `source_document_id`
  - `source_page`
  - `source_text` (verbatim string snippet)
  - `status`: `VERIFIED_FROM_DOCUMENT`

---

## 3. Existing Calculations Review

| Calculation | Inputs | Current Implementation | Current Output | Formula / Rule | Validation Check | Source Record |
|---|---|---|---|---|---|---|
| **Reconciled Closing** | `opening_balance`, `transactions` | Float addition & subtraction in `validator_layer.py` | `calculated_closing` (float) | $Closing = Opening + Credits - Debits$ | Discrepancy $\le 0.05$ | Bank Statement Page 1 & 4 |
| **Total Income** | All transactions with `type == 'CREDIT'` | `sum(float(tx['amount']))` in `calculator.py` | `total_income` (float) | $\sum Credits$ | Must match sum of verified credit rows | Document Line Items |
| **Total Expenses** | All transactions with `type == 'DEBIT'` | `sum(float(tx['amount']))` in `calculator.py` | `total_expenses` (float) | $\sum Debits$ | Must match sum of verified debit rows | Document Line Items |
| **Net Savings** | `total_income`, `total_expenses` | `round(total_income - total_expenses, 2)` | `monthly_savings` (float) | $Income - Expenses$ | Arithmetic check | Calculated from Credits and Debits |
| **Savings Rate** | `savings`, `total_income` | `round((savings / total_income * 100), 1)` | `savings_rate` (%) | $(Savings / Income) \times 100$ | Guarded against division by zero ($Income > 0$) | Derived metric |
| **Category Totals** | Transaction category amounts | Dictionary accumulation in `calculator.py` | `categories` breakdown | $\sum Amount_{category}$ | Sum of categories equals Total Expenses | Line Item Classifications |
| **Emergency Buffer** | `savings` | Rule: `10000.0 if savings >= 10000.0 else max(1000.0, round(savings * 0.4, 2))` | `recommended_emergency_buffer` | Heuristic allocation rule | Non-negative, $\le Savings$ | Rule Engine |

---

## 4. Existing Weaknesses & Gaps Identified

### 4.1 Monetary Value Precision (Floating-Point Arithmetic)
- **Problem**: `float` is used in `extractor.py`, `normalizer.py`, `validator_layer.py`, `calculator.py`, and `server.py`.
- **Architectural Decision**: Adopt Python's standard `decimal.Decimal` with fixed 2 decimal places (`ROUND_HALF_UP`) for all financial calculations and conversions. Store amounts in SQLite as exact decimal strings or reals without precision loss.

### 4.2 Ambiguous Direction & Missing Transaction Types
- **Problem**: Current system only supports `CREDIT` and `DEBIT`.
- **Requirement**: Must distinguish `CREDIT`, `DEBIT`, `REFUND`, `REVERSAL`, and `TRANSFER`.
- **Handling**:
  - `REFUND`: E.g. Merchant refund (Swiggy, Amazon). Decreases expense rather than inflating earned income.
  - `REVERSAL`: E.g. Failed transaction auto-reversal or chargeback.
  - `TRANSFER`: E.g. Self-transfer between user accounts (e.g. Savings to Demat or UPI to personal account). Must not be double counted as both income and expense.
  - If ambiguous, mark as `direction = NEEDS_REVIEW`.

### 4.3 Overlapping Statements & Transaction-Level Duplicates
- **Problem**: Ingestion currently checks SHA-256 hash of the entire PDF file. If a user uploads Statement A (Oct 1 - Oct 31) and later uploads Statement B (Oct 15 - Nov 15), SHA-256 allows Statement B, resulting in double-counting transactions between Oct 15 and Oct 31!
- **Requirement**: Implement transaction fingerprinting:
  $Fingerprint = SHA256(Date + ISO\_Amount + Direction + Cleaned\_Merchant + Masked\_Account)$
  Transactions matching an existing fingerprint for the same account must be classified as `DUPLICATE_CONFIRMED` and excluded from financial summaries to avoid double-counting.

### 4.4 Date Formatting & ISO-8601 Standardization
- **Problem**: `02/10/2024` is stored as-is. Sorting lexicographically in SQL puts `02/10/2024` next to `02/11/2024`.
- **Requirement**: Convert all dates to standard `YYYY-MM-DD` while preserving raw extracted string for provenance.

### 4.5 Calculation Module Structure
- **Problem**: Calculations currently reside inside `app/ingestion/calculator.py` and some ad-hoc logic in `app/server.py` (`_execute_advisory_inquiry`).
- **Requirement**: Create a dedicated, clean financial engine under `app/financial/`:
  - `app/financial/money.py`: Safe `Money` and `Decimal` arithmetic utilities.
  - `app/financial/normalization.py`: Strict schema, direction classification, ISO date parsing.
  - `app/financial/reconciliation.py`: Mathematical reconciliation and audit checks.
  - `app/financial/calculations.py`: Deterministic financial metrics (Cash flow, income, expenses, savings, categories).
  - `app/financial/duplicate.py`: Transaction fingerprinting and overlap resolution.

---

## 5. Architectural Design for Phase 3

### 5.1 Financial Engine Module Organization
```text
app/financial/
├── __init__.py
├── money.py               # Safe Money class backed by Decimal (ROUND_HALF_UP)
├── models.py              # Typed dataclasses/schemas for NormalizedTransaction, ReconciliationReport
├── normalization.py       # ISO date parsing, direction inference, merchant cleaning, status assignment
├── reconciliation.py      # Deterministic bank reconciliation engine
├── calculations.py        # Core metrics: Cash Flow, Income, Expenses, Savings Rate, Category Aggregation
└── duplicate.py           # Transaction fingerprinting & overlapping statement deduplication
```

### 5.2 Safe Money Representation
```python
from decimal import Decimal, ROUND_HALF_UP

def to_decimal(val: Any) -> Decimal:
    """Safely converts string, int, float, or Decimal to a 2-decimal-place Decimal."""
    if isinstance(val, Decimal):
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    # Strip currency symbols, commas, spaces
    clean_str = str(val).replace(',', '').replace('₹', '').replace(' ', '').strip()
    return Decimal(clean_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

### 5.3 Overlapping Statement Handling
When processing a new document:
1. Extract line items.
2. Generate SHA-256 fingerprint for each transaction:
   `sha256(f"{date_iso}|{amount_decimal}|{direction}|{merchant_clean}|{account_id}")`.
3. Check existing transactions for the same user and account:
   - If fingerprint exists $\rightarrow$ tag as `DUPLICATE_CONFIRMED`, link to existing transaction ID.
   - If date overlaps with an existing statement period but fingerprint is unique $\rightarrow$ retain as `UNIQUE`.
4. In `compute_financial_profile`, filter out `DUPLICATE_CONFIRMED` transactions from calculations.

### 5.4 Golden Dataset Definition
Create `app/tests/fixtures/golden_statements.py` containing:
1. `HDFC_GOLDEN_VALID`: The active 4-page statement (₹45,500 opening, ₹82,000 credit, ₹54,300 debit, ₹73,200 closing).
2. `STATEMENT_OVERLAP_PAIR`: Statement 1 (Oct 1 - Oct 20) and Statement 2 (Oct 15 - Oct 31) with known shared transactions.
3. `STATEMENT_DISCREPANCY`: Statement with missing ₹3,200 transaction $\rightarrow$ flags `NEEDS_REVIEW`.
4. `STATEMENT_REFUND_REVERSAL`: Statement with ₹420 Swiggy refund and ₹500 ATM reversal $\rightarrow$ correctly offsets expenses.
5. `STATEMENT_INTERNAL_TRANSFER`: Transfer of ₹25,000 between user's own accounts $\rightarrow$ classified as `TRANSFER`.

---

## 6. Verification & Test Plan

1. **Precision & Money Tests**:
   - Verify floating-point traps (e.g. `0.1 + 0.2`, `1,27,500.00 - 420.00`) produce exact Decimal outputs.
   - Zero, negative, and large INR values (up to ₹10 Crore) tested without overflow.
2. **Reconciliation Tests**:
   - Perfect statement $\rightarrow$ `READY`, discrepancy = `Decimal('0.00')`.
   - Missing or extra transactions $\rightarrow$ `NEEDS_REVIEW`, discrepancy highlighted.
   - Reversals and refunds $\rightarrow$ reconciled accurately.
3. **Transaction Normalization & Deduplication Tests**:
   - Overlapping statements do NOT inflate monthly income or expenses.
   - Direction accurately tagged (`CREDIT`, `DEBIT`, `REFUND`, `REVERSAL`, `TRANSFER`).
   - Ambiguous items tagged as `NEEDS_REVIEW`.
4. **Phase 2 Security Regression Tests**:
   - Re-run all 21 existing tests to ensure zero security regressions.

---

## 7. Next Step: Execution Plan

1. Create `app/financial/` package and modules (`money.py`, `models.py`, `normalization.py`, `reconciliation.py`, `calculations.py`, `duplicate.py`).
2. Integrate `app/financial/` into `app/ingestion/pipeline.py` and `app/server.py`.
3. Update `app/db.py` to support `direction`, `transaction_fingerprint`, and ISO dates.
4. Build golden fixtures and comprehensive unit test suite in `app/tests/test_financial_engine.py`.
5. Execute test suite and verify 100% pass rate.
6. Author `docs/PHASE_3_COMPLETION_REPORT.md` and sync documentation.

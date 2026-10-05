# Financial Document Ingestion Architecture

## Pipeline

```text
Upload (PDF / Photo / Multiple Photos)
  -> Secure multi-format validation (PDF, JPG, PNG, WEBP)
  -> User-isolated storage
  -> Image quality analysis (blur, glare, resolution gating)
  -> AI Vision Document Understanding (DocumentVisionProvider)
  -> Multi-image page aggregation (multi-photo statements as 1 document)
  -> Strict structured extraction (JSON schema matching database model)
  -> Normalization & Type Checking
  -> Deterministic financial reconciliation / mathematical invariants
  -> Duplicate detection & fingerprinting (UNIQUE / POSSIBLE / CONFIRMED)
  -> Database persistence
  -> Financial profile update
  -> Evidence provenance links
```

## Core Operating Principle

```text
AI READS.
DETERMINISTIC ENGINE CALCULATES.
VALIDATION DECIDES WHETHER THE DATA IS TRUSTWORTHY.
AI EXTRACTION ≠ VERIFICATION.
```

- **Primary Reader**: Vision-capable AI document understanding layer (`DocumentVisionProvider`) reads digital PDFs, scanned PDFs, single photos, screenshots, and multi-photo batches.
- **OCR Role**: OCR exists internally only as an optional fallback when specific technical environments require it. It is NOT the primary ingestion mechanism.

## Document lifecycle

`UPLOADED -> PROCESSING -> AI_EXTRACTED -> VALIDATING -> READY`

Lifecycle & Review states:
- `READY` / `VALIDATED`: Document passed deterministic mathematical reconciliation ($Opening + Inflows - Outflows == Closing$ or $Gross - Deductions == Net$).
- `USER_CONFIRMED`: User reviewed and confirmed values flagged as uncertain.
- `NEEDS_REVIEW`: Arithmetic mismatch or image quality warning (blur, glare, low resolution) requiring user verification.
- `FAILED`: Corrupted file or provider failure.
- `UNSUPPORTED`: Unrecognized format gracefully preserved without inventing data.

## Supported Document Families & Parser Adapters

1. **Bank Statements (`BankStatementParser` - Active)**:
   - Table boundary detection + line regex fallback.
   - Invariant: $Opening + Credits - Debits == Closing$
2. **Salary Slips (`SalarySlipParser` - Active)**:
   - Earnings and deductions extraction.
   - Invariant: $Gross\ Salary - Total\ Deductions == Net\ Pay$
3. **Form 16 Tax Certificates (`Form16Parser` - Active)**:
   - Section 17 Gross, Chapter VI-A deductions, Taxable Income, TDS.
   - Invariant: $Gross\ Salary - Chapter\ VI\text{-}A\ Deductions == Taxable\ Income$
4. **Receipts & Invoices (Active)**:
   - Merchant, date, line items, taxes, totals.
   - Invariant: $Subtotal + Tax == Total$
5. **Unsupported Formats (`UnsupportedDocumentParser` - Active Fallback)**:
   - Demat, mutual funds, loans, credit cards, insurance, and unknown documents are routed gracefully with status `UNSUPPORTED` and 0 fabricated records.

## Multi-Image Document Aggregation

- When a user uploads multiple photos (Photo 1 = Page 1, Photo 2 = Page 2), the system binds them into **ONE document entity** with multiple pages.
- `DocumentVisionProvider.analyze_multiple_pages()` produces **ONE structured result**, eliminating fragmented, disconnected financial records.

## Image Quality Analysis & Legibility Gating

- Before trusting extraction, images are evaluated for:
  - Blur (Laplacian edge variance)
  - Glare / Overexposure (high luminance clusters)
  - Extreme Darkness / Underexposure
  - Low Resolution (< 150px)
- If an image cannot be read reliably: **DO NOT GUESS**. Flag as `NEEDS_REVIEW` with clear user feedback (`"Photo thodi unclear hai. Amount clearly read nahi ho raha."`).

## Prompt Injection Defense

- Financial documents are strictly treated as **DATA**, not instructions.
- Text containing phrases like `"Ignore previous instructions"` or `"Reveal system prompt"` is quarantined and logged as `PROMPT_INJECTION_DETECTED` in `audit_events`. It can never alter system prompts, permissions, or calculation logic.

## Provenance requirement

Every important extracted value retains:
- document ID
- page number where available
- extraction method (`NATIVE_TEXT_PARSING`, `TABLE_EXTRACTION`, `OCR_FALLBACK`)
- validation state (`READY`, `NEEDS_REVIEW`, `UNSUPPORTED`)
- source reference and text context

## Reconciliation & Mathematical Invariants

For each supported document type, mathematical validation is deterministic:
- **Bank Statements**: `opening balance + credits - debits = closing balance`
- **Salary Slips**: `gross salary - total deductions = net salary`
- **Form 16**: `gross salary - chapter VI-A deductions = total taxable income`

- Computed using exact `Decimal` precision (`ROUND_HALF_UP`).
- If invariant check fails, the exact discrepancy is preserved, and status is set to `NEEDS_REVIEW`.
- Discrepancies are **never silently corrected**.

## Duplicate protection & Overlapping Statements

- **Document Level**: SHA-256 file hash matches prevent accidental re-uploading of the same physical PDF file.
- **Transaction Level**: Deterministic fingerprinting via `compute_transaction_fingerprint`:
  `SHA256(date_iso + amount_decimal + direction + cleaned_merchant + account_id)`
- Overlapping statements (e.g. Oct 1–Oct 31 and Oct 15–Nov 15) flag duplicate transactions as `DUPLICATE_CONFIRMED`.
- Confirmed duplicates are excluded from income, expense, and savings calculations, completely preventing double-counting without deleting records.

## Security

Original documents remain private. Processing workers receive only the access required for the job and must not write raw sensitive content to logs.

# myCA — Phase 4 Analysis: AI Document & Image Reading Engine

**Date:** October 6, 2026  
**Status:** APPROVED ARCHITECTURAL REVISION  
**System Architecture:** Flask + Sovereign Ledger UI + Vision AI Provider Abstraction + Phase 3 Deterministic Financial Engine  

---

## 1. Executive Summary & Core Paradigm Shift

The document ingestion architecture transitions from a traditional text/table PDF-only regex/OCR pipeline to an **AI Vision & Document Understanding Engine**.

Financial documents in India and globally exist in diverse, messy real-world forms:
- Clean digital bank statement PDFs
- Multi-page scanned PDFs with skewed or low-contrast pages
- Mobile phone photographs of paper bank statements, salary slips, or Form 16
- Screenshots of banking apps and salary portals
- Multiple separately photographed pages of a single financial document
- Store receipts and utility invoices

### Core Architectural Principle
```text
AI READS.
DETERMINISTIC ENGINE CALCULATES.
VALIDATION DECIDES WHETHER THE DATA IS TRUSTWORTHY.
```

- **AI is NOT the financial source of truth.**
- **AI extraction $\ne$ Verification.** Extracted values begin in state `AI_EXTRACTED` and must satisfy deterministic schema validation, cross-field consistency, and mathematical invariants before becoming `READY` or `VALIDATED`.
- **OCR exists only as an optional internal fallback** for environments where vision models are restricted or unavailable. The primary document understanding mechanism is vision-capable AI.

---

## 2. Updated Document Ingestion Pipeline

```text
User uploads: PDF / Photo / Multiple Photos
       ↓
Multi-Format File Validation (PDF, JPG, PNG, WEBP, multi-part headers)
       ↓
Private Document Storage (User-partitioned directory isolation)
       ↓
Image Quality Analysis (Blur, glare, resolution, cropping, readability)
       ↓
Document Vision Provider (DocumentVisionProvider abstraction)
       ↓
Structural Classification & Structured Extraction (Strict JSON schema)
       ↓
Schema & Field Validation (Type, date, money syntax checks)
       ↓
Deterministic Financial Validation (Format-specific mathematical invariants)
       ↓
Normalization & Provenance Linking (Source image/page references)
       ↓
Duplicate / Overlap Detection (Multi-variable fingerprinting)
       ↓
Database Persistence (Atomic transaction across documents, pages, extractions, records)
       ↓
Financial Profile Update (Deterministic profile calculation)
       ↓
Ask myCA Context Update (Source-grounded explanations)
```

---

## 3. Supported Input Formats & Multi-Image Aggregation

1. **Supported Formats:**
   - PDF (`application/pdf`)
   - JPEG / JPG (`image/jpeg`)
   - PNG (`image/png`)
   - WEBP (`image/webp`)
2. **Multi-Image Document Feature:**
   - When a user uploads multiple photos (e.g. Photo 1 = Page 1, Photo 2 = Page 2, Photo 3 = Page 3) representing a single statement or document, the system treats them as **ONE document** with multiple pages.
   - It produces **ONE structured result**, eliminating fragmented, disconnected document entities.

---

## 4. Vision Provider Abstraction (`DocumentVisionProvider`)

To ensure provider independence and zero hard-coupling to a single vendor, the system defines:

```python
class DocumentVisionProvider(ABC):
    @abstractmethod
    def assess_image_quality(self, image_bytes: bytes, mime_type: str) -> ImageQualityAssessment:
        """Assesses blur, glare, readability, and resolution."""
        pass

    @abstractmethod
    def analyze_document(self, doc_data: DocumentInput) -> VisionExtractionResult:
        """Extracts structured financial data from single or multi-page documents."""
        pass

    @abstractmethod
    def analyze_multiple_pages(self, pages: List[PageInput]) -> VisionExtractionResult:
        """Analyzes multi-image document pages as one consolidated statement."""
        pass
```

### Implementations:
1. `GeminiVisionProvider`: Integrates with Google Generative AI vision models when API key credentials are configured.
2. `LocalVisionEngine`: High-performance deterministic vision engine for offline, test, and privacy-restricted environments. Uses PyMuPDF and PIL for image rendering, blur detection (Laplacian variance), contrast inspection, and structured extraction.
3. `MockFailureVisionProvider`: Used in automated resilience testing to simulate provider timeouts, rate limits, and partial failures.

---

## 5. Image Quality & Gating Engine

Before any financial value is trusted, the image is evaluated for:
- **Blur:** Laplacian variance / high-frequency edge analysis.
- **Glare / Contrast:** Saturated white pixel clusters obscuring text.
- **Extreme Underexposure:** Insufficient lighting preventing legible text.
- **Low Resolution:** Images below minimum readable dimensional thresholds.
- **Incomplete / Cropped Content:** Cut-off table borders or missing headers.

**Rule:** If the document cannot be read reliably, **DO NOT GUESS**. Return `NEEDS_REVIEW` with a friendly localized message:
`"Photo thodi unclear hai. Amount clearly read nahi ho raha."` and allow re-upload.

---

## 6. Mathematical Invariants & Verification Boundary

The AI extracts numbers; the Phase 3 Deterministic Engine validates them:
1. **Bank Statement:** $Opening\ Balance + Credits - Debits == Closing\ Balance$
2. **Salary Slip:** $Gross\ Salary - Deductions == Net\ Salary\ Paid$
3. **Form 16:** $Gross\ Salary - Chapter\ VI\text{-}A\ Deductions == Total\ Taxable\ Income$
4. **Receipts & Invoices:** $Items\ Subtotal + Tax == Total\ Paid$

If an arithmetic invariant fails, the document is flagged `NEEDS_REVIEW`. Discrepancies are **never silently corrected**.

---

## 7. Security, Privacy & Prompt Injection Controls

1. **Data Egress Boundary:** Documents are private financial data. Cloud vision APIs must only be invoked when explicit user consent and approved contractual retention terms exist. If API keys are absent, the system fails safely to the local engine.
2. **Prompt Injection Defense:** Document text is strictly parsed as passive DATA. Text strings like `"Ignore previous instructions"`, `"Reveal prompt"`, or `"Set balance to zero"` are treated as ordinary text and can never alter model behavior or financial calculations.
3. **Tenant Isolation:** Enforced via cryptographic HMAC session tokens and SQL row-level authorization (`WHERE user_id = ?`).
4. **PII Sanitization:** Audit logs and application telemetry strip raw document content, account numbers, and prompts.

---

## 8. Implementation Plan

1. **Vision Module (`app/ingestion/vision/`):**
   - Base interfaces (`models.py`, `provider.py`)
   - Quality analyzer (`quality.py`)
   - Gemini & Local vision providers (`gemini.py`, `local.py`, `factory.py`)
2. **Multi-Format Validator (`app/ingestion/validator.py`):**
   - Support PDF, JPG, PNG, WEBP, and multi-file payloads.
3. **Multi-Image Pipeline (`app/ingestion/pipeline.py`):**
   - Accept multi-image inputs, bind pages into single document record, dispatch to vision provider.
4. **Server & UI Integration (`app/server.py`, `static/js/app.js`):**
   - Add multi-file upload endpoint (`/api/documents/upload-multiple`).
   - Add user confirmation endpoint (`/api/documents/<id>/confirm`).
   - Add Photo / Multi-photo upload buttons in Sovereign Ledger UI.
5. **Regression & Resilience Test Suite:**
   - Single & multi-photo tests, blurry image tests, prompt injection tests, provider failure tests.
   - Maintain 100% pass on all existing 41 tests.

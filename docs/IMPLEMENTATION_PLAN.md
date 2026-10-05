# myCA — Detailed Implementation Plan

> **Standard:** Mandated by Phase 5 of `MYCA — DOCUMENTATION-FIRST PROJECT INTEGRATION PROMPT`.  
> **Status:** Pre-Implementation Plan (Approval Gate)  
> **Date:** October 2026

---

## Roadmap by Phase & Dependency

```text
Phase 1: Documentation & Architecture Baselining
   │
   ▼
Phase 2: Foundation & Security Hardening
   │
   ▼
Phase 3: Database & Data Model Alignment
   │
   ▼
Phase 4: Document / PDF Ingestion Pipeline
   │
   ▼
Phase 5: Deterministic Financial Engine
   │
   ▼
Phase 6: Financial UI Integration (Sovereign Ledger)
   │
   ▼
Phase 7: Knowledge & Regulatory Retrieval
   │
   ▼
Phase 8: AI / Agent Layer & Tool Permissions
   │
   ▼
Phase 9: Ask myCA Grounded Advisory
   │
   ▼
Phase 10: Testing & Security Hardening
   │
   ▼
Phase 11: Production Deployment Readiness
```

---

### PHASE 1: Documentation + Architecture Baselining
- **Objectives:** Establish the documentation foundation as the project's single source of truth; reconcile existing prototype code with target architecture.
- **Files to Create:**
  - `docs/ANALYSIS_REPORT.md`
  - `docs/ARCHITECTURE_RECONCILIATION.md`
  - `docs/IMPLEMENTATION_PLAN.md`
- **Files to Modify:**
  - `README.md` (Update project status and navigation index)
- **Database Changes:** None.
- **API Changes:** None.
- **Dependencies:** None.
- **Tests:** Verify docs tree structure and Markdown integrity.
- **Security Considerations:** Ensure no sensitive secrets or credentials exist in documentation.
- **Definition of Done:** All 3 analysis/plan documents are committed and reviewed; Phase 6 gate is ready for sign-off.

---

### PHASE 2: Foundation & Security Hardening (STATUS: COMPLETE)
- **Objectives:** Implement server-side authenticated context, HMAC-SHA256 session tokens, short-lived signed URLs, prompt injection defenses, versioned statutory knowledge, and IDOR protection.
- **Files Created:**
  - `app/security.py` (HMAC session tokens, signed doc tokens, `@require_auth` decorator, `LocalPrivateStorage`)
  - `app/audit.py` (Structured sanitized audit event logger)
  - `app/knowledge/tax_registry.py` (Versioned Statutory Knowledge Model)
  - `app/tests/test_cross_user_security.py` (15 automated cross-user isolation and authorization tests)
  - `docs/PHASE_2_COMPLETION_REPORT.md` (Formal Phase 2 verification report)
- **Files Modified:**
  - `app/server.py` (Hardened with `@require_auth`, signed URLs, and API contract aliases)
  - `app/db.py` (Added `audit_events` and `statutory_rules` tables, WAL mode, test users)
  - `app/ingestion/pipeline.py` (Private storage routing, audit records, prompt injection logging)
  - `app/ingestion/extractor.py` (Adversarial regex detection patterns)
  - `static/js/app.js` & `static/js/viewer.js` (Session token handling and signed PDF iframe URLs)
- **Database Changes:**
  - Created table `audit_events` (security and operational audit log with PII redaction)
  - Created table `statutory_rules` (versioned statutory knowledge model)
- **API Changes:**
  - Added `POST /api/auth/token` for cryptographic session token generation
  - Added `GET /api/documents/:id/signed-url` for short-lived (300s) private document access
  - Added aliases matching `docs/api/API_CONTRACTS.md`
- **Tests Passed:**
  - 21/21 automated tests passed (15 cross-user isolation tests + 6 pipeline regression tests)
- **Definition of Done:** Passed release-blocking gate proving User A cannot read or modify User B data.

---

### PHASE 3: Financial Calculation Engine & Extraction Intelligence (STATUS: COMPLETE)
- **Objectives:** Build and harden the deterministic financial calculation and document-extraction intelligence layer with Decimal precision, statement overlap deduplication, and transaction direction classification.
- **Files Created:**
  - `docs/PHASE_3_ANALYSIS.md` (Detailed analysis of extraction and calculations)
  - `app/financial/money.py` (Safe Decimal currency representation and Indian number formatting)
  - `app/financial/models.py` (Typed dataclasses and enums for transactions and reconciliation)
  - `app/financial/normalization.py` (ISO date parsing, merchant cleaning, direction inference)
  - `app/financial/reconciliation.py` (Deterministic balance reconciliation with zero float errors)
  - `app/financial/calculations.py` (Net cash flow, savings rate, transfers isolation)
  - `app/financial/duplicate.py` (SHA-256 transaction fingerprinting and overlap deduplication)
  - `app/tests/fixtures/golden_statements.py` (Golden test fixtures for standard and edge-case statements)
  - `app/tests/test_financial_engine.py` (Unit and golden fixture regression suite)
  - `docs/PHASE_3_COMPLETION_REPORT.md` (Formal Phase 3 audit and completion report)
- **Files Modified:**
  - `app/db.py` (Added `direction`, `date_iso`, `fingerprint`, `duplicate_status`, `duplicate_of_id`)
  - `app/ingestion/pipeline.py` (Integrated `app.financial` engine and transaction deduplication)
  - `app/server.py` (Integrated `compute_financial_profile_deterministic`)
  - `docs/data/DATA_MODEL.md` (Documented Phase 3 transaction fields)
  - `docs/architecture/DOCUMENT_INGESTION.md` (Documented Decimal reconciliation and overlap deduplication)
- **Database Changes:**
  - Added columns `date_iso`, `direction`, `fingerprint`, `duplicate_status`, `duplicate_of_id` to `transactions` table.
- **Tests Passed:**
  - 29/29 automated tests passed (8 financial engine tests + 15 cross-user security tests + 6 pipeline regression tests)
- **Definition of Done:** Deterministic calculations run on exact Decimal arithmetic, overlap deduplication prevents double-counting, and Phase 2 security remains 100% verified.

---

### PHASE 4: AI Document & Image Reading Engine (STATUS: COMPLETE)
- **Objectives:** Build an AI vision and document understanding engine supporting digital PDFs, scanned PDFs, single photographs (JPG/PNG/WEBP), and multi-image documents (multiple photos consolidated into one document entity) with pluggable `DocumentVisionProvider`, image quality gating (blur/glare/low-res), prompt injection defense, and user review confirmation.
- **Files Created:**
  - `docs/PHASE_4_ANALYSIS.md` (Comprehensive AI Vision pre-implementation analysis)
  - `app/ingestion/vision/__init__.py` (Vision module initialization and exports)
  - `app/ingestion/vision/models.py` (Typed dataclasses for vision results and quality assessments)
  - `app/ingestion/vision/quality.py` (Laplacian variance blur, luminance glare, and resolution analyzer)
  - `app/ingestion/vision/provider.py` (Abstract `DocumentVisionProvider` interface)
  - `app/ingestion/vision/local.py` (`LocalVisionEngine` for offline/air-gapped processing and multi-page aggregation)
  - `app/ingestion/vision/gemini.py` (`GeminiVisionProvider` utilizing Google Generative AI vision)
  - `app/ingestion/vision/factory.py` (Dynamic provider factory with fallback handling)
  - `app/tests/test_vision_engine.py` (Comprehensive 10-test AI vision suite)
  - `docs/PHASE_4_COMPLETION_REPORT.md` (Formal 17-section Phase 4 completion report)
- **Files Modified:**
  - `app/ingestion/validator.py` (Support for PDF, JPG, PNG, WEBP, and multi-file payloads)
  - `app/ingestion/pipeline.py` (Integrated vision provider, multi-image document consolidation, review gating)
  - `app/server.py` (Added `POST /api/documents/upload-multiple` and `POST /api/documents/<id>/confirm`)
  - `static/index.html` (Added `[PDF upload karein]`, `[Photo upload karein]`, `[Multiple photos]` buttons)
  - `static/js/app.js` (Multi-photo upload handler, understood financial card, review confirm dialog)
  - `app/tests/fixtures/golden_statements.py` (Added synthetic image fixtures: blur, glare, low-res, prompt injection)
- **Tests Passed:**
  - 51/51 automated tests passed (10 vision engine + 12 multi-format ingestion + 8 financial engine + 15 cross-user security + 6 pipeline regression tests).
- **Definition of Done:** AI vision reads PDFs and photos, multiple photos are merged into single document entities, poor quality images gate to `NEEDS_REVIEW`, deterministic engine validates all values, and 100% test pass with zero regressions.

---

### PHASE 5: Financial Knowledge & Grounded Intelligence Foundation (STATUS: COMPLETE)
- **Objectives:** Build the knowledge and grounded-intelligence foundation that allows myCA to answer financial questions using validated user data, authoritative versioned knowledge, deterministic calculations, and source evidence with zero guessing.
- **Files Created:**
  - `docs/PHASE_5_ANALYSIS.md` (Pre-implementation architectural analysis)
  - `app/knowledge/models.py` (Typed models for statutory rules, advisory responses, tax breakdowns)
  - `app/knowledge/tax_calculator.py` (Cent-exact Decimal tax calculation engine for New and Old regimes)
  - `app/advisory/__init__.py` (Advisory package exports)
  - `app/advisory/models.py` (Advisory data contracts)
  - `app/advisory/intent.py` (Intent classification and prompt injection defense)
  - `app/advisory/engine.py` (Grounded advisory orchestrator and multi-tenant evidence binder)
  - `app/tests/test_knowledge_registry.py` (10 tests for versioning, supersession, and tax calculation)
  - `app/tests/test_grounded_advisory.py` (11 tests for golden questions, multi-tenant isolation, prompt injection)
  - `docs/PHASE_5_COMPLETION_REPORT.md` (Formal 17-section completion and compliance report)
- **Files Modified:**
  - `app/db.py` (Added `topic`, `title`, `content`, `version` columns to `statutory_rules`)
  - `app/knowledge/tax_registry.py` (Official legislative rules for AY 2025-26 & AY 2024-25, search, ingestion guard)
  - `app/financial/calculations.py` (Hardened credit/debit direction inference against column defaults)
  - `app/server.py` (Integrated `GroundedAdvisoryEngine` and added `GET /api/advisory/tax-estimate`)
  - `static/js/app.js` (Added interactive `[Kaise nikala?]` audit evidence drill-down)
- **Tests Passed:**
  - 72/72 automated tests passed (10 knowledge registry + 11 grounded advisory + 10 vision + 12 multi-format ingestion + 8 financial engine + 15 cross-user security + 6 pipeline regression tests).
- **Definition of Done:** Ask myCA answers are grounded strictly in user documents and statutory rules; zero LLM math; prompt injection defense verified; multi-tenant isolation verified; 100% test pass.

---

### PHASE 6: Financial UI Integration (Sovereign Ledger)
- **Objectives:** Ensure the web interface preserves the Sovereign Ledger aesthetic while dynamically rendering verified data.
- **Files to Modify:**
  - `static/index.html` (Home, Money, Ask myCA, Vault, Evidence Drawer, PDF Viewer)
  - `static/js/app.js` (State sync, router, category editor, Hinglish progress reporting)
  - `static/js/viewer.js` (PDF viewer with page jumping and citation highlighting)
  - `static/css/styles.css` (Sovereign Ledger color tokens and typography)
- **Database Changes:** None.
- **API Changes:** None.
- **Dependencies:** Tailwind CSS CDN (preserved from Stitch export).
- **Tests:**
  - Verify display of Home values: ₹27,700 left, ₹82,000 aaya, ₹54,300 gaya, ₹27,700 saved.
  - Verify Source Evidence Drawer shows exact document, page number, and raw text on click.
  - Verify Built-in PDF Viewer opens to target page (e.g. Page 4 for Rent).
- **Security Considerations:** Sanitize all dynamic HTML injections against XSS attacks using `escapeHtml`.
- **Definition of Done:** UI displays verified document data with zero placeholder values and complete responsive layout.

---

### PHASE 7: Knowledge & Regulatory Retrieval
- **Objectives:** Implement a versioned repository for statutory tax rules and deduction caps.
- **Files to Create:**
  - `data/knowledge/statutory_registry.json` (Finance Act 2024 tax slabs, Section 80C caps, rebate under 87A)
  - `app/knowledge.py` (Versioned retrieval service matching assessment year)
- **Files to Modify:**
  - `app/server.py` (Integrate knowledge lookups)
- **Database Changes:** None.
- **API Changes:**
  - Expose `GET /api/knowledge/rules?ay=2024-25`
- **Dependencies:** None.
- **Tests:**
  - Verify retrospective rule retrieval for AY 2024-25 vs AY 2023-24.
- **Security Considerations:** Statutory rules must be immutable and digitally versioned.
- **Definition of Done:** Versioned statutory rules are accessible with effective dates and official citations.

---

### PHASE 8: AI / Agent Layer & Tool Permissions
- **Objectives:** Build the constrained orchestrator and read-only specialist agent tools adhering to least-privilege principles.
- **Files to Create:**
  - `app/agents/orchestrator.py` (Constrained agent routing)
  - `app/agents/tools.py` (Strictly typed tools: `query_user_transactions`, `get_statutory_rule`, `calculate_surplus`)
- **Files to Modify:** None.
- **Database Changes:** None.
- **API Changes:** None.
- **Dependencies:** Standard JSON schema validation.
- **Tests:**
  - Verify that agent tools cannot execute arbitrary SQL queries.
  - Verify prompt injection defenses against malicious document text.
- **Security Considerations:** AI is strictly a reasoning and explanation interface; state-changing mutations require explicit user confirmation.
- **Definition of Done:** Agent tools are strictly permissioned and refuse actions outside authorized scopes.

---

### PHASE 9: Ask myCA Grounded Advisory
- **Objectives:** Enable natural conversational financial inquiries grounded strictly in verified document data.
- **Files to Modify:**
  - `app/server.py` (Expose `POST /api/ask` returning answers with structured statutory citations)
  - `static/js/app.js` (Render citation badges linking directly to PDF viewer pages)
- **Database Changes:** None.
- **API Changes:**
  - Standardize `POST /api/ask` payload: `{ query: string } \rightarrow { answer: string, sources: [{ source, page, status, snippet }] }`
- **Dependencies:** None.
- **Tests:**
  - Query: *"Mera paisa sabse zyada kahan ja raha hai?"* $\rightarrow$ Assert answer highlights Rent (₹18,000) with citation to Page 4.
  - Query with insufficient data $\rightarrow$ Assert refusal response: *"Mere paas abhi iske liye enough information nahi hai."*
- **Security Considerations:** Context passed to advisory query contains only the authenticated user's records.
- **Definition of Done:** All Ask myCA answers include auditable document citations or explicit refusal when data is absent.

---

### PHASE 10: Testing & Security Hardening
- **Objectives:** Execute exhaustive integration, financial correctness, security, and edge-case testing.
- **Files to Create:**
  - `app/tests/test_golden_statements.py` (Golden dataset of varied statement formats)
  - `app/tests/test_security_idor.py` (Exhaustive IDOR and multi-tenant boundary checks)
- **Files to Modify:**
  - `app/tests/test_pipeline.py` (Expand coverage)
- **Database Changes:** None.
- **API Changes:** None.
- **Dependencies:** Python `unittest`.
- **Tests:**
  - Multi-tenant isolation: User A vs User B data leakage test.
  - Malformed PDF, password-protected PDF, and empty file test.
  - Duplicate ingestion test.
  - Reconciliation discrepancy test.
- **Security Considerations:** Zero critical vulnerabilities or IDOR paths.
- **Definition of Done:** 100% of automated test suites pass without regression.

---

### PHASE 11: Production Deployment Readiness
- **Objectives:** Prepare the containerized deployment assets and environment configurations.
- **Files to Create:**
  - `Dockerfile` (Lightweight Python container running Gunicorn)
  - `.env.example` (Template of all environment variables)
- **Files to Modify:**
  - `docs/engineering/DELIVERY_AND_DEPLOYMENT.md` (Update deployment runbook)
- **Database Changes:** None.
- **API Changes:** None.
- **Dependencies:** `gunicorn`.
- **Tests:**
  - Container build and health-check verification.
- **Security Considerations:** Zero secrets baked into container image.
- **Definition of Done:** Application builds cleanly into a reproducible container image.


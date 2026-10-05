# myCA — Architecture Reconciliation Document

> **Standard:** Mandated by Phase 4 of `MYCA — DOCUMENTATION-FIRST PROJECT INTEGRATION PROMPT`.  
> **Status:** Architectural Reconciliation Baseline  
> **Date:** October 2026

---

## 1. What Architecture Exists Today?

Today, myCA operates as a unified, single-service Python/Flask application serving a decoupled modern vanilla web frontend:

- **Frontend Tier:**
  - Modern HTML5, Vanilla JavaScript (`app.js`, `viewer.js`), and Tailwind CSS utility styling implementing the **Sovereign Ledger** visual language.
  - Composed of 4 consolidated views: Home, Money, Ask myCA, and Document Vault.
  - Interactive components: Slide-out Source / Evidence Drawer, Built-in PDF Viewer Modal, Drag-and-Drop Ingestion modal with Hinglish progress reporting, Category Correction dialog.
- **Application & API Tier:**
  - Lightweight Python Flask service (`app/server.py`) handling document upload, PDF streaming, user financial profiles, transaction filtering, and grounded Q&A.
- **Ingestion & Calculation Engine:**
  - `app/ingestion/`: Pipeline orchestrating validation, SHA-256 duplicate checking, PyMuPDF text/table extraction, normalizer, mathematical reconciliation audit ($Opening + Credits - Debits = Closing$), and category rollup.
- **Data Persistence:**
  - SQLite database (`data/myca.db`) implementing 13 normalized tables with tenant isolation (`user_id`).
  - Private filesystem storage (`data/uploads/<user_id>/`) for original PDFs.

---

## 2. What Architecture Should myCA Have?

According to `MASTER_CONTEXT.md` and `docs/architecture/SYSTEM_ARCHITECTURE.md`:

```text
Web / Mobile UI (Sovereign Ledger)
      │
      ▼
Application API Layer
      │
      ├─ Authenticated Context & Authorization (Session / JWT)
      ├─ Financial Domain Services (Ledgers, Accounts, Passbook)
      ├─ Document Ingestion Engine (Validation, Extraction, Fallback OCR, Reconciliation)
      ├─ Deterministic Financial Engine (Strictly isolated mathematical truth)
      ├─ Versioned Statutory Knowledge Layer (Auditable citations with effective dates)
      ├─ Constrained AI Advisory Orchestrator (Least-privilege tool execution)
      └─ Audit & Observability (Security logs, IDOR defense, Rate limits)
      │
      ▼
PostgreSQL (Row-Level Security) + Private Encrypted Object Storage
```

---

## 3. What Can Remain?

The following existing components are aligned with product principles and should **remain intact**:

1. **Sovereign Ledger Visual Language & UI Assets:**
   - The Warm Ivory (`#FBFBF9`), Deep Midnight Slate (`#0F172A`), Forest Evergreen (`#065F46`), and Muted Amber palette.
   - Newsreader optical serif headings paired with Manrope tabular numerals.
   - Clean, quiet editorial luxury feel with zero AI spark or robot tropes.
2. **Deterministic Mathematical Reconciliation Engine:**
   - Strict audit logic ($Opening + Credits - Debits = Closing$).
   - Refusal to silently correct arithmetic errors; explicit flagging as `NEEDS_REVIEW`.
3. **PyMuPDF Ingestion Core:**
   - Fast, local, private, and deterministic parsing of PDF text and tables without third-party network leakage.
4. **Source Provenance & Evidence Linking Architecture:**
   - Retaining `document_id`, `page_number`, and `source_text` on every financial value.
   - Ability to jump directly from a figure to its source page in the built-in PDF viewer.
5. **Existing Normalized Data Schema Structure:**
   - Separation into `documents`, `document_pages`, `financial_accounts`, `transactions`, `income_records`, `expense_records`, `loans`, and `investments`.

---

## 4. What Needs Modification?

1. **API Route Harmonization:**
   - Align current routes with `docs/api/API_CONTRACTS.md`:
     - Expose `/api/documents` (for upload as well as listing) alongside `/api/documents/upload`.
     - Expose `/api/financial/summary`, `/api/financial/transactions`, and `/api/financial/accounts`.
     - Expose `/api/ask` as standard endpoint for Ask myCA advisory.
2. **Audit Logging:**
   - Add `audit_events` logging to track document deletions, category updates, and authentication state transitions.
3. **Authentication Handshake:**
   - Transition from arbitrary client header `X-User-ID` to verified session middleware.
4. **Scanned PDF Handling:**
   - Extend the existing scan-detection heuristic with an OCR fallback hook when image-only PDFs are uploaded.

---

## 5. What Needs to be Newly Created?

1. **`audit_events` Table & Logger:**
   - Record user ID, event type (`DOCUMENT_UPLOADED`, `CATEGORY_MODIFIED`, `DOCUMENT_DELETED`), timestamp, and IP/correlation ID.
2. **API Contract Aliasing Layer:**
   - Add compatibility wrappers in `app/server.py` to seamlessly serve both the internal prototype routes and the documented API contract specification.
3. **Statutory Knowledge Manifest:**
   - Versioned JSON registry for statutory reference data (e.g., Section 80C deduction limit ₹1,50,000, Section 115BAC New Tax Regime slab structure for FY 2024-25 / AY 2025-26).
4. **Golden Evaluation Test Suite (`docs/qa/`):**
   - Formal test fixtures with known statement values and reconciliation assertions.

---

## 6. What Should NOT Be Built Yet?

To avoid unnecessary over-engineering and architectural bloat (as explicitly mandated by `docs/architecture/SYSTEM_ARCHITECTURE.md` and `docs/engineering/TOOLING_AND_ENVIRONMENTS.md`), the following must **NOT** be built yet:

- ❌ **No Microservices Architecture:** Maintain a modular monolith; premature distributed services add operational fragility without customer value.
- ❌ **No Redis / Memcached Cache:** Database query performance on normalized SQLite/Postgres is under 2ms for user-scoped data; caching introduces cache invalidation risks.
- ❌ **No Kafka / Event Bus:** Document processing jobs run efficiently in-process or via simple background threads.
- ❌ **No Vector Database (Pinecone, Weaviate, Qdrant):** Structured financial transactions are relational and tabular; vector similarity search on financial arithmetic introduces hallucination risks.
- ❌ **No Autonomous Multi-Agent Swarm:** Multiple autonomous agents debating financial numbers violate the determinism principle. Keep a single constrained orchestrator with specialized deterministic tools.
- ❌ **No Live Market Ticker Integrations:** Personal tax and wealth governance relies on monthly/quarterly closing positions, not sub-second tick feeds.

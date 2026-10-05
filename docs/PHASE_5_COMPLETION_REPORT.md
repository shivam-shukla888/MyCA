# myCA — Phase 5 Completion Report: Financial Knowledge & Grounded Intelligence Foundation

**Date:** October 6, 2026  
**Status:** COMPLETE & FULLY VERIFIED  
**Test Suite:** 72 / 72 Automated Tests Passing (0 Regressions across Phase 2, Phase 3, Phase 4, and Phase 5)  
**System Architecture:** Sovereign Ledger Visual Language + Deterministic Financial Engine + Versioned Statutory Knowledge Model (`statutory_rules`) + Grounded Advisory Orchestrator (`GroundedAdvisoryEngine`)  

---

## Executive Summary

Phase 5 has implemented the **Financial Knowledge and Grounded Intelligence Foundation** for myCA. Ask myCA can now answer complex personal finance questions grounded strictly in:
1. User's validated financial data (scoped row-level to authenticated `user_id`)
2. Authoritative, versioned statutory knowledge (gazetted tax acts, deduction caps, and official circulars)
3. Deterministic calculations (exact Decimal Python arithmetic)
4. Verifiable source evidence with clickable audit links

### Operating Philosophy
```text
MYCA SHOULD NEVER SOUND MORE CERTAIN THAN ITS EVIDENCE.
AI IS THE INTERFACE.
THE FINANCIAL ENGINE IS THE CALCULATOR.
THE AUTHORITATIVE SOURCE IS THE KNOWLEDGE AUTHORITY.
THE USER'S VALIDATED DATA IS THE PERSONAL FINANCIAL TRUTH.
VALIDATION IS THE TRUST BOUNDARY.
```

The system strictly avoids the insecure antipattern:
$$\text{User Financial Data} \longrightarrow \text{LLM} \longrightarrow \text{Hallucinated / Guess Response}$$

Instead, the operational pipeline is:
$$\text{User Data} + \text{Authoritative Knowledge} + \text{Deterministic Calculations} \longrightarrow \text{Grounded, Auditable myCA Response}$$

---

## 1. Knowledge Architecture

The financial intelligence foundation is structured into two non-overlapping, strictly separated operational planes:

```text
┌────────────────────────────────────────────────────────┐
│                   ASK MYCA ADVISORY                    │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   USER FINANCIAL PLANE   │  │    STATUTORY KNOWLEDGE   │
├──────────────────────────┤  ├──────────────────────────┤
│ - bank_statements        │  │ - statutory_rules table  │
│ - salary_slips           │  │ - Central Acts (Finance) │
│ - form_16_certificates   │  │ - Gazette Notifications  │
│ - transactions           │  │ - CBDT / RBI Circulars   │
│ - Scoped to user_id      │  │ - Global Read-Only       │
│ - Private & Confidential │  │ - Immutable & Versioned  │
└─────────────┬────────────┘  └─────────────┬────────────┘
              │                             │
              └─────────────┬───────────────┘
                            ▼
              ┌───────────────────────────┐
              │   DETERMINISTIC ENGINE    │
              │  - Decimal Tax Slabs      │
              │  - Rebate u/s 87A         │
              │  - Standard Deduction     │
              │  - Cash Flow & Savings    │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │ GROUNDED ADVISORY ENGINE  │
              │  - Intent & Sanitization  │
              │  - Evidence Aggregator    │
              │  - "Kaise nikala?" Audit  │
              └───────────────────────────┘
```

---

## 2. Source Hierarchy

To eliminate hallucinated tax rules, an explicit source hierarchy is enforced:

1. **Primary Official Sources**:
   - Central Legislation: *The Finance (No. 2) Act, 2024 (Act No. 15 of 2024)*, *The Finance Act, 2023*, *Income-tax Act, 1961*.
   - Gazette of India Notifications (e.g. *Gazette Notification No. 22/2024*).
   - Official CBDT circulars and statutory orders.
2. **Versioned Knowledge Record**:
   - Seeded into the `statutory_rules` database table with publication date, effective date span, applicable Assessment Year, and section citations.
3. **Deterministic Unit Tests**:
   - Python test cases asserting exact tax slabs, standard deductions, and rebate boundaries.
4. **Deterministic Calculation Code**:
   - `app/knowledge/tax_calculator.py` executing cent-exact Decimal arithmetic.
5. **myCA Human Language Explanation**:
   - Conversational framing conveying the deterministic result without modifying any numeric values.

Secondary sources (blogs, commentary, social media posts) are **never** permitted to override or write to primary knowledge. Any unverified rule is marked `NOT_VERIFIED` and barred from calculation.

---

## 3. Versioning Model

The `statutory_rules` database schema (`app/db.py`) enforces full lifecycle tracking:

| Field | Type | Function |
| :--- | :--- | :--- |
| `id` | `TEXT PRIMARY KEY` | e.g. `rule_sec_115bac_ay25_26` |
| `topic` | `TEXT` | `INCOME_TAX`, `DEDUCTION`, `REBATE` |
| `title` | `TEXT` | Human-readable provision title |
| `content` | `TEXT` | Legal summary of the section |
| `source` | `TEXT` | Regulatory authority (e.g. *Ministry of Law and Justice*) |
| `official_source_reference`| `TEXT` | Act and Gazette citation |
| `publication_date` | `TEXT` | Gazette notification date (`YYYY-MM-DD`) |
| `effective_from` | `TEXT` | Start date of applicability |
| `effective_to` | `TEXT` | End date (or `NULL` if ongoing) |
| `financial_year` | `TEXT` | e.g. `2024-25` |
| `assessment_year` | `TEXT` | e.g. `2025-26` |
| `provision` | `TEXT` | Specific section (e.g. *Section 115BAC(1A)*) |
| `jurisdiction` | `TEXT` | `IN_CBDT` |
| `status` | `TEXT` | `CURRENT`, `FUTURE`, `SUPERSEDED`, `NOT_VERIFIED` |
| `rule_data_json` | `TEXT` | Structured parameters (slabs, standard deductions, rebate caps) |
| `supersedes` | `TEXT` | Link to superseded rule (e.g. `rule_sec_115bac_ay24_25`) |
| `superseded_by` | `TEXT` | Forward link to superseding rule |
| `version` | `INTEGER` | Monotonic schema version |

### Active Versioned Tax Rules:
- **AY 2025-26 (New Regime)**: `rule_sec_115bac_ay25_26` — Slabs: 0-3L (0%), 3-7L (5%), 7-10L (10%), 10-12L (15%), 12-15L (20%), >15L (30%). Enhanced Standard Deduction: ₹75,000. Section 87A rebate up to ₹7,00,000 taxable income. Status: `CURRENT`. Supersedes `rule_sec_115bac_ay24_25`.
- **AY 2024-25 (New Regime)**: `rule_sec_115bac_ay24_25` — Slabs: 0-3L (0%), 3-6L (5%), 6-9L (10%), 9-12L (15%), 12-15L (20%), >15L (30%). Standard Deduction: ₹50,000. Status: `SUPERSEDED`. Superseded by `rule_sec_115bac_ay25_26`.
- **Section 80C Ceiling**: `rule_sec_80c_cap` — Aggregate deduction ceiling ₹1,50,000 for EPF, PPF, ELSS, Life Insurance under Old Tax Regime. Status: `CURRENT`.
- **Section 80D Health**: `rule_sec_80d_health` — Health insurance premia up to ₹25,000 (self/family) + ₹25,000/₹50,000 (parents). Status: `CURRENT`.
- **Section 24(b) Home Loan**: `rule_sec_24b_home_loan` — Interest on borrowed capital up to ₹2,00,000 for self-occupied home property. Status: `CURRENT`.
- **Unverified Proposal**: `rule_draft_unverified_reform` — Speculative draft rumor. Status: `NOT_VERIFIED`. Excluded from advisory calculations.

---

## 4. Retrieval Architecture (Deterministic vs. Vector DB)

In accordance with architectural guidelines, **heavy vector databases (Pinecone, Qdrant, Weaviate, pgvector) were deliberately rejected**:

| Evaluation Parameter | Heavy Vector RAG | Deterministic Knowledge Registry (Implemented) |
| :--- | :--- | :--- |
| **Precision** | Semantic similarity risks pulling superseded AY 2024-25 slabs for AY 2025-26 queries | Cent-exact filtering on exact `assessment_year` and `status = 'CURRENT'` |
| **Hallucination Risk** | Embeddings blend disparate chunks | Zero blending; parameters are passed directly to deterministic calculation functions |
| **Latency** | 200–800 ms | $< 2\text{ ms}$ (indexed SQLite queries) |
| **System Complexity** | High external SaaS dependency, API key risk | Embedded SQLite, 100% offline, zero operational cost |
| **Auditability** | Opaque similarity scores | Full provenance: exact rule ID, section, and gazette notification attached |

---

## 5. User-Data Isolation

Multi-tenant isolation is enforced at the database layer:
1. **Cryptographic Identity**: Requests must provide an HMAC-SHA256 session token signed by the server. The token extracts `g.user_id`.
2. **SQL Scoping**: All personal financial queries enforce row-level filtering:
   ```sql
   SELECT * FROM transactions WHERE user_id = ?
   SELECT * FROM income_records WHERE user_id = ? AND status IN ('READY', 'VERIFIED_FROM_DOCUMENT', 'USER_CONFIRMED')
   SELECT * FROM documents WHERE user_id = ?
   ```
3. **Isolation Verification**: Unit tests (`test_08_multi_tenant_user_isolation` and `test_13_ask_myca_context_is_isolated`) verify that Client B (Priya) querying the advisory desk receives `NO_USER_DATA` and cannot see any of Client A's (Aarav's) transactions, documents, or income.

---

## 6. Calculation Boundary

All mathematical and financial operations are restricted to deterministic Python engines:
- **`app/financial/calculations.py`**:
  - Net Savings = Total Income - Total Expenses
  - Savings Rate = (Net Savings / Total Income) * 100
  - Category Allocations & Descending Expense Breakdown
- **`app/knowledge/tax_calculator.py`**:
  - Standard deduction deduction ($Gross - 75,000$)
  - Progressive slab evaluation across 6 income tiers
  - Section 87A full tax rebate evaluation (Tax = 0 for taxable income $\le$ ₹7,00,000)
  - 4% Health and Education Cess addition
  - Exact Python `Decimal` arithmetic with `ROUND_HALF_UP`

**Strict Rule**: An LLM or AI model is **never** permitted to calculate totals, compute tax amounts, or adjust balances.

---

## 7. AI Boundary & Prompt Injection Defense

AI operations are strictly confined to:
1. Understanding user queries and extracting intent
2. Formatting structured facts into natural, warm, and professional user-facing language

### Prompt Injection Defense:
- All incoming user queries and document snippets are scanned by `app/advisory/intent.py` against adversarial prompt injection patterns (`"ignore previous instructions"`, `"reveal system prompt"`, `"override security"`, `"unrestricted mode"`).
- Adversarial attempts are intercepted immediately, logged as `PROMPT_INJECTION_DETECTED` in `audit_events`, and returned as a safe `WARNING` message: *"Aapka sawal process nahi kiya ja sakta. Kripya valid personal financial sawal puchein."*

---

## 8. Evidence & Provenance ("Kaise nikala?")

Every Ask myCA response returns a structured contract (`GroundedAdvisoryResponse`):

```json
{
  "answer": "Aapki verified income ke annualized hisaab (₹984,000) par New Tax Regime (Section 115BAC, AY 2025-26) ke tehat standard deduction (₹75,000) ke baad estimated tax ₹42,536 banta hai.",
  "response_type": "CALCULATION",
  "data_used": {
    "annual_gross": 984000.0,
    "standard_deduction": 75000.0,
    "taxable_income": 909000.0,
    "tax_payable": 42536.0
  },
  "knowledge_used": [
    {
      "id": "rule_sec_115bac_ay25_26",
      "official_source_reference": "The Finance (No. 2) Act, 2024 (Act No. 15 of 2024), Gazette of India Notification No. 22/2024"
    }
  ],
  "calculation_used": "₹984,000 (Gross) - ₹75,000 (Std Ded) = ₹909,000 (Taxable) -> Slab Tax + 4% Cess = ₹42,536",
  "sources": [
    {
      "source": "Section 115BAC(1A), The Finance (No. 2) Act, 2024",
      "source_type": "STATUTORY_RULE",
      "reference_id": "rule_sec_115bac_ay25_26",
      "page": null,
      "status": "STATUTORY_CURRENT",
      "snippet": "Standard Deduction: ₹75,000, 5-10-15-20-30% Slabs, Rebate up to ₹7,00,000"
    },
    {
      "source": "Salary Slip (Infosys Limited)",
      "source_type": "USER_DOCUMENT",
      "reference_id": "doc_salary_01",
      "page": 1,
      "status": "VERIFIED_FROM_DOCUMENT",
      "snippet": "Monthly Income: ₹82,000 (Annualized: ₹984,000)"
    }
  ],
  "status": "GROUNDED_AND_VERIFIED"
}
```

### UI Interaction:
- In the Sovereign Ledger UI, clicking `[Kaise nikala? (Audit Evidence)]` reveals the exact formula, personal data used, and statutory citation.
- Verified document buttons permit users to click directly to the document page in the PDF viewer.

---

## 9. Comprehensive Test Suite (72 / 72 Passing)

The test suite executed with **zero errors and zero failures**:

```text
Ran 72 tests in 4.262s

OK
```

### Test Suite Breakdown:
1. **`app/tests/test_knowledge_registry.py` (10 / 10 Passing)**:
   - Official legislative source provenance
   - Supersession links (AY 2024-25 $\rightarrow$ AY 2025-26)
   - Current rules filtering (superseded and unverified exclusion)
   - Quarantining `NOT_VERIFIED` rules
   - Ingestion validation guard
   - Exact New Regime AY 2025-26 calculation math
   - Section 87A rebate calculation (₹0 tax up to ₹7.75L gross)
   - Superseded AY 2024-25 differential calculation
   - Old Regime deduction caps (Section 80C, 80D, 24(b))
   - Effective date filtering
2. **`app/tests/test_grounded_advisory.py` (11 / 11 Passing — Golden Question Dataset)**:
   - Financial summary inquiry ("Kitna paisa bacha?")
   - Highest expense inquiry ("Mera paisa sabse zyada kahan ja raha hai?")
   - Verified salary slip inquiry ("Meri salary kitni aayi?")
   - Tax inquiry with Section 115BAC statutory rule cited
   - Emergency fund recommendation with explicit FACT vs. RECOMMENDATION separation
   - Section 80C education inquiry
   - Missing data gating (foreign income / crypto $\rightarrow$ `NEEDS_INFO`, no guessing)
   - Multi-tenant context isolation (User Priya cannot see User Aarav's data)
   - Prompt injection defense in user queries
   - `POST /api/ask` contract blueprint
   - `GET /api/advisory/tax-estimate` endpoint verification
3. **Phase 4 Vision Tests (`test_vision_engine.py`)**: 10 / 10 Passing
4. **Phase 3 Financial & Multi-Format Tests (`test_financial_engine.py`, `test_ingestion_multi_format.py`, `test_pipeline.py`)**: 20 / 20 Passing
5. **Phase 2 Security & Isolation Tests (`test_cross_user_security.py`, `test_security.py`)**: 21 / 21 Passing

---

## 10. Phase 2 Regression Results

All 21 Phase 2 security foundation tests remain 100% green:
- `test_cross_user_security.py`: 15 / 15 Passing
- `test_security.py`: 6 / 6 Passing
- Cryptographic HMAC session tokens, row-level SQL isolation, and signed document tokens verified.

---

## 11. Phase 3 Regression Results

All 20 Phase 3 financial engine and multi-format tests remain 100% green:
- Cent-exact Decimal arithmetic verified.
- Balance reconciliation ($Opening + Inflows - Outflows == Closing$) verified.
- Overlapping statement deduplication with multi-variable fingerprinting verified.

---

## 12. Phase 4 Regression Results

All 10 Phase 4 AI Vision tests remain 100% green:
- Multi-image document aggregation (Photo 1 + Photo 2 = 1 document entity) verified.
- Image quality gating (blur, glare, resolution) verified.
- Provider abstraction (`DocumentVisionProvider`) verified.

---

## 13. Security Review

- **Data Egress**: Pure local deterministic knowledge lookup; zero user financial records are transmitted to third-party endpoints during statutory tax advisory.
- **Log Sanitization**: PII, passwords, full PAN numbers, and raw prompt texts are redacted from audit logs.
- **Query Quarantine**: Prompt injection attempts are logged to `audit_events` and rejected before entering processing.

---

## 14. Cost & Performance Observations

- **Zero API Cost for Common Inquiries**: Common financial questions (savings, rent, food expenses, highest expense, tax slabs, emergency fund) are computed locally via deterministic SQL and Decimal Python in $< 5\text{ ms}$ at $\$0.00$ API cost.
- **Query Latency**: Advisory response generation runs in $< 15\text{ ms}$ locally.

---

## 15. Known Limitations

1. **Complex Business Income**: Surcharge on income above ₹50 Lakhs and presumptive business income (Section 44AD/ADA) are planned for future phases.
2. **Multi-Year Historical Comparison**: Historical year comparison is currently supported across AY 2024-25 and AY 2025-26; earlier years (AY 2023-24 and prior) require additional historical statutory seeds.

---

## 16. Open Decisions

1. **User Confirmation of Suggested Categories**: Whether manual category overrides should trigger an advisory re-indexing notification or update silently.
2. **Capital Gains Integration**: Schedule for incorporating Schedule 112A equity LTCG (12.5% rate under Finance (No. 2) Act, 2024) into the tax calculator.

---

## 17. Recommendations for Next Phase (Phase 6)

1. **End-to-End User Experience & Sovereign Ledger Polish**:
   - Deepen interactive charts and category timeline visualizers.
   - Refine the dual-regime tax comparison card in the Money tab.
2. **Automated Tax Optimization Suggestions**:
   - Provide side-by-side comparison between Old Regime (with 80C/80D/24b deductions) and New Regime (Section 115BAC), showing the exact rupee savings.

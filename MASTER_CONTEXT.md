# myCA — Master Context

> Documentation-first foundation. Implementation MUST NOT begin until the pre-implementation agent analysis protocol is completed.

## Product principle

**Har insaan ka apna CA.**

myCA is intended to become a personal financial operating system: a simple interface over a much more rigorous financial/data/security engine.

### Core UX rule

**Complex engine → simple interface.**

Every important screen should make these three things obvious:
1. Meri financial situation kya hai?
2. Kya important hai?
3. Ab mujhe kya karna chahiye?

## Documentation order

1. `product/PRODUCT_PRINCIPLES.md`
2. `architecture/SYSTEM_ARCHITECTURE.md`
3. `architecture/DOCUMENT_INGESTION.md`
4. `data/DATA_MODEL.md`
5. `design/DESIGN_SYSTEM.md`
6. `design/ICON_AND_CONTENT_SYSTEM.md`
7. `security/SECURITY_POLICY.md`
8. `security/FINANCIAL_SAFETY_POLICY.md`
9. `ai/AGENT_ARCHITECTURE.md`
10. `ai/AGENT_ANALYSIS_PROTOCOL.md`
11. `api/API_CONTRACTS.md`
12. `engineering/TOOLING_AND_ENVIRONMENTS.md`
13. `qa/QA_AND_EVALUATION.md`
14. `engineering/DELIVERY_AND_DEPLOYMENT.md`
15. `OPEN_DECISIONS.md`

## Mandatory implementation gate

The implementation agent must first:
- read this file;
- read all referenced docs;
- inspect the existing repository;
- inspect the Stitch screens/components;
- identify conflicts, missing requirements and security risks;
- produce an analysis report and implementation plan;
- stop for validation/approval before making irreversible architecture changes.

No agent may silently invent requirements.


## Source of truth: uploaded Stitch ZIP

The current Stitch export contains:
- `home_myca_financial_operating_system/code.html` + screenshot
- `money_net_worth_cash_flow_ledgers/code.html` + screenshot
- `goals_wealth_milestones_simulator/code.html` + screenshot
- `ask_myca_private_advisory_desk/code.html` + screenshot
- `sovereign_ledger/DESIGN.md`

Observed design-system facts:
- Surface foundation: `#f9f9f7`
- Primary: `#000000`
- Primary container: `#131b2e`
- Secondary: `#486458`
- Secondary container: `#c7e7d7`
- Tertiary container: `#331200`
- Error: `#ba1a1a`
- On-surface: `#1a1c1b`
- Fonts: Newsreader for display/headlines; Manrope for body, labels and numerals.
- Desktop display size in the source system: 48px / 56px.
- Mobile display size: 36px / 44px.
- Spacing tokens include 4px, 8px, 16px, 24px and 40px equivalents.
- Rounded tokens are 4px, 8px, 12px, 16px, 24px and full.
- The design uses Material Symbols for icons.
- The visual philosophy is quiet, authoritative and human, and explicitly rejects neon gradients, luminous shadows and AI-spark/robot visual tropes.
